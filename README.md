# Buying Frenzy

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ssurbhi560/buying-frenzy/Buying%20Frenzy%20CI?logo=github&style=for-the-badge)](https://github.com/ssurbhi560/buying-frenzy/actions/workflows/CI.yml)
[![Codecov](https://img.shields.io/codecov/c/github/ssurbhi560/buying-frenzy?logo=codecov&style=for-the-badge&token=7XI27PTPR1)](https://codecov.io/gh/ssurbhi560/buying-frenzy)
![Code Style (Black)](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/ssurbhi560/frenzy?logo=docker&sort=semver&style=for-the-badge)](https://hub.docker.com/r/ssurbhi560/frenzy)

> GraphQL Backend for a food delivery platform.

## Usage
```shell
$ poetry install
$ poetry run python -m flask run
```

Using Docker :

```shell
$ docker pull ssurbhi560/frenzy:<TAG>
$ docker run -p 5000:5000 -d --rm ssurbhi560/frenzy:<TAG> -e "ELASTICSEARCH_URL=<ELASTICSEARCH_URL>" -e "SECRET_KEY=<SECRET_KEY>" --name frenzy
```

This should start a server at http://localhost:5000/graphql.

For running tests:

```shell
$ poetry run python -m pytest
$ # Or with coverage tracking information:
$ poetry run python -m coverage run -m pytest
$ poetry run python -m coverage html  # writes an html report to htmlcov/index.html.
```

### Load data

Running `flask seed-db` loads data from the provided [restaurants](https://gist.githubusercontent.com/seahyc/b9ebbe264f8633a1bf167cc6a90d4b57/raw/021d2e0d2c56217bad524119d1c31419b2938505/restaurant_with_menu.json) and [users](https://gist.githubusercontent.com/seahyc/de33162db680c3d595e955752178d57d/raw/785007bc91c543f847b87d705499e86e16961379/users_with_purchase_history.json) database. To change these values, specify new values for the following environment variables (you may change them in `.flaskenv`):

```
RESTAURANT_DATA_URL=""
USER_DATA_URL=""
```

and run: 

```shell
$ flask seed-db
```

For docker installation, execute the following after running the container:
```shell
$ docker exec frenzy flask seed-db
```

## API 

1. To get all restaurants:
    ```graphql
    query {
        restaurants {
            edges {
                node {
                    name
                    cashBalance
                }
            }
        }
    }
    ```
    Get all the restaurants that are open at a certain datetime (in ISO format):
    ```graphql
    query {
        restaurants(openAt:"2022-02-20T21:03:00.00765") {
            edges {
                node {
                    name
                    cashBalance
                }
            }
        }
    }
    ```
1. List all the restaurants that have more or less than x number of dishes within a price range.

    ```graphql
    query {
        restaurants(minPrice: 10, maxPrice: 15, minDishes: 2) {
            edges {
                node {
                    name
                    cashBalance
                }
            }
        }
    }
    ```
    Or, for less than _`x`_ number of dishes specify the `maxDishes` argument instead:
    ```graphql
    query {
        restaurants(minPrice: 10, maxPrice: 15, maxDishes: 4) {
            edges {
                node {
                    name
                    cashBalance
                }
            }
        }
    }
    ```
    To limit the number of restaurants (top _`y`_), you may specify the `first` argument:
    ```graphql
    query {
        restaurants(first: 10, minPrice: 10, maxPrice: 15, minDishes: 2) {
            edges {
                node {
                    name
                    cashBalance
                }
            }
        }
    }
    ```
    Note that specifying both `maxDishes` and `minDishes` arguments will result in an error. Similarly, not specifying any one of `minDishPrice` or `maxDishPrice` will also raise an error.
1. To search for a restaurant/dish, pass the `q` argument to `search` query. It returns a `SearchResult` type which is a `Union` of `Restaurant` and `Dish` types: therefore, fragments are required for making conditional selections. The search is fuzzy, and can automatically detect typos/related words, e.g. searching for `Surbhi` also shows results for `Sushi`:
    ```graphql
    query {
        search(q:"Surbhi") {  # Shows results for 'Sushi' xD
            ... on Restaurant {
                id
                name
                cashBalance
            }
            ... on Dish {
                id
                name
                price
            }
        }
    }
    ```
1. Process a user purchasing a dish from a restaurant:
    ```graphql
    mutation {
        purchase(input: {userId: "VXNlcjox", dishId: "RGlzaDoz"}) {
            order {
                id
                dishName
                transactionAmount
                transactionDate
                restaurantName
                userId
                restaurantId
            }
        }
    }
    ```
    The `ID` of the corresponding dish/user may be found by selecting them:
    ```graphql
    query {
        # Get id of all users.
        users {
            edges {
                node {
                    id
                }
            }
        }
        # Get id of all dishes from all restaurants.
        restaurants {
            edges {
                node {
                    dishes {
                        edges {
                            node {
                                id
                            }
                        }
                    }
                }
            }
        }
    }
    ```

## References:

1. Miguel Grinberg's famous [tutorial on Flask](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). This is my go-to website whenever I'm bootstrapping a new project.
1. This tutorial on [flask-graphene-sqlalchemy](https://github.com/alexisrolland/flask-graphene-sqlalchemy/wiki/Flask-Graphene-SQLAlchemy-Tutorial#mutations-examples) from @alexisrolland was also very helpful.
