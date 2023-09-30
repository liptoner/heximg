### Development

Uses the default Django development server.

1. Rename *.env.dev-sample* to *.env.dev*.
1. Update the environment variables in the *docker-compose.yml* and *.env.dev* files.
1. Build the images and run the containers:

    ```sh
    $ docker-compose up -d --build
    ```

    Test it out at [http://localhost:8000](http://localhost:8000). The "app" folder is mounted into the container and your code changes apply automatically.

To prepare account just use:
* `docker-compose exec app bash`
* `python manage.py createsuperuser` 
* `python manage.py switchuserplan --username=admin --plan=Basic`

The **switchuserplan** command that makes it easier to switch between predefinied (in core migrations) plans.
