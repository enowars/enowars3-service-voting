import sys
import getopt
from pathlib import Path
import subprocess


def __print_usage() -> None:
    print("Usage: checker_setup.py -i <service_id> -n <service_name> -m <python_module> [-d]")
    print()
    print("Creates the files needed for your checker to be run in our docker swarm production environment.")
    print("It should be save to use as it skips files that already exist.")
    print()
    print("-i, --id\tUnique Service ID, e.g. '9'")
    print("-n, --name\tUnique Service Name, e.g. 'voting'")
    print("-m, --module\tChecker python module/file, e.g. 'checker.py'")
    print("-d, --deploy\tExecute docker commands for deployment after creating files")


def __setup_file(filename, content) -> None:
    path = Path.cwd() / filename

    if path.exists():
        print("Skipped {}.".format(filename))
        return

    file = path.open(mode="w")

    for line in content:
        file.write(line)

    file.close()

    print("Wrote {}.".format(path))


def __setup_docker_compose_yml() -> None:
    __setup_file("docker-compose.yml", [
        "version: '3'\n",
        'services:\n',
        '  {}-backend:\n'.format(service_name),
        '    build: .\n',
        '    image: 10.13.37.7:5000/{}-backend\n'.format(service_name),
        '    networks:\n',
        '     - bridge\n',
        '     - enoverlay\n',
        '    environment:\n',
        '     - MONGO_ENABLED=1\n',
        '     - MONGO_HOST=checkerdb_mongo_1\n',
        '     - MONGO_PORT=27017\n',
        '     - MONGO_USER=ipv6islove\n',
        '     - MONGO_PASSWORD=dockerislove\n',
        '  {}-frontend:\n'.format(service_name),
        '    image: nginx:1.13-alpine\n',
        '    volumes:\n',
        '      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n',
        '    depends_on:\n',
        '      - {}-backend\n'.format(service_name),
        '    networks:\n',
        '      - enoverlay\n',
        '    labels:\n',
        '        - "traefik.enable=true"\n',
        '        - "traefik.backend={}-checker"\n'.format(service_name),  # TODO: not sure if this is correct
        '        - "traefik.docker.network=enoverlay"\n',
        '        - "traefik.frontend.rule=Host:{}.checker.enowars.com,service{}.checker.enowars.com"\n'.format(
            service_name, service_id),
        '        - "traefik.port=80"\n',
        'networks:\n',
        '  bridge:\n',
        '    external: true\n',
        '  enoverlay:\n',
        '    external: true\n'
    ])


def __setup_dockerfile() -> None:
    __setup_file("Dockerfile", [
        'FROM python\n',
        '\n',
        '# Install uswgi\n',
        'RUN pip3 install uwsgi\n',
        '\n',
        'WORKDIR /checker\n',
        '\n',
        '# install requirements\n',
        'COPY ./requirements.txt /checker/requirements.txt\n',
        'RUN pip3 install -r requirements.txt\n',
        '\n',
        '# copy our files in\n',
        'COPY ./uwsgi.ini uwsgi.ini\n',
        '\n',
        '# here you might need to add more stuff\n',
        'COPY ./{} {}\n'.format(checker_module, checker_module),
        '\n',
        'ENTRYPOINT ["uwsgi", "--uid", "uwsgi", "--socket", "[::]:3031", "--protocol", "uwsgi", "--ini", "./uwsgi.ini"]\n'
    ])


def __setup_nginx_conf() -> None:
    __setup_file("nginx.conf", [
        'server {\n',
        '    resolver 127.0.0.11 ipv6=off;\n',
        '    listen 80 default_server;\n',
        '    location / {\n',
        '        try_files $uri @wsgi;\n',
        '    }\n',
        '\n',
        '    location @wsgi {\n',
        '        set $target {}-checker_{}-backend;\n'.format(service_name, service_name),
        '        include uwsgi_params;\n',
        '        uwsgi_pass $target:3031;\n',
        '    }\n',
        '}\n'
    ])


def __setup_requirements() -> None:
    __setup_file("requirements.txt", ['git+https://github.com/domenukk/enochecker\n'])


def __setup_uswgi_ini() -> None:
    __setup_file("uwsgi.ini", [
        '[uwsgi]\n',
        'enable-threads = true\n',
        'module = {}\n'.format(checker_module[:-3]),  # stripping away '.py'
        'callable = app\n',
        'uid = root\n',
        'gid = root\n',
        '\n',
        'cheaper-algo = spare2\n',
        'cheaper = 200\n',
        '# number of workers to spawn at startup\n',
        'cheaper-initial = 50\n',
        '# maximum number of workers that can be spawned\n',
        'workers = 2000\n',
        '# how many workers should be spawned at a time\n',
        'cheaper-step = 20\n'
    ])


if __name__ == "__main__":
    # parse command line arguments and fail on wrong usage
    service_id = None
    service_name = None
    checker_module = None
    deploy = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhi:n:m:", ["deploy", "id=", "name=", "module="])
    except getopt.GetoptError:
        __print_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            __print_usage()
            sys.exit(0)
        elif opt in ("-i", "--id"):
            service_id = arg
        elif opt in ("-n", "--name"):
            service_name = arg
        elif opt in ("-m", "--module"):
            checker_module = arg
        elif opt in ("-d", "--deploy"):
            deploy = True

    if service_name is None or service_id is None or checker_module is None:
        __print_usage()
        sys.exit(2)

    # write the files
    __setup_docker_compose_yml()
    __setup_dockerfile()
    __setup_nginx_conf()
    __setup_requirements()
    __setup_uswgi_ini()

    # build, push and deploy
    if deploy:
        try:
            print("Running sudo docker-compose build...")
            subprocess.run(["sudo", "docker-compose", "build"], check=True)

            print("Running sudo docker-compose push...")
            subprocess.run(["sudo", "docker-compose", "push"], check=True)

            print(
                "Running sudo docker stack deploy --compose-file docker-compose.yml {}-checker...".format(service_name))
            subprocess.run(["sudo", "docker", "stack", "deploy", "--compose-file", "docker-compose.yml",
                            "{}-checker".format(service_name)], check=True)
        except subprocess.CalledProcessError:
            sys.exit()
