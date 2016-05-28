# PyMock
[![GPL Licence][licence-badge]](LICENSE)

PyMock is a simple mock REST API written with Flask. Use if you need a mock API in seconds.

# Installation
For Python 2.x:
```sh
$ pip install -r requirements/python2.txt
```

For Python 3.x:
```sh
$ pip install -r requirements/python3.txt
```

# Usage
Just type:
```sh
$ python app.py
```
Voila!

You can start using your mock API now.


# What does it do?

Think about a simple blog REST API. It stores users and blog posts. You get an access token and log into the API, then manage a simple blog.


# Methods

| Method           | Path             | Action                                  | Parameters       | Headers          |
| ---------------- | ---------------- | --------------------------------------- | ---------------- | ---------------- |
| **GET**          | /v1              | Main endpoint and returns API's status. | -                | -                |
| **POST**         | /v1/login        | Logs into the API.                      | username: **String**<br>password: **String** | **Content-Type:** application/json |
| **GET**          | /v1/users        | Returns all users.                      | -                | -                |
| **GET**          | /v1/users/:id    | Returns a user with the given ID.       | -                | -                |
| **POST**         | /v1/users        | Creates a new user.                     | username: **String**<br>password: **String**<br>name: **String**<br>email: **String** | **Content-Type:** application/json |
| **DELETE**       | /v1/users/:id    | Deletes a user.                         | -                | **Authorization:** Token |
| **PATCH**        | /v1/users/:id    | Updates user's information.             | *Fields in /v1/login* | **Authorization:** Token |
| **GET**          | /v1/posts        | Returns all blog posts.                 | -                | -                |
| **GET**          | /v1/posts/:id    | Returns a blog post with the given ID.  | -                | -                |
| **POST**         | /v1/posts        | Creates a new blog post.                | title: **String**<br>content: **String**<br>tags: **String** | **Authorization:** Token<br>**Content-Type:** application/json |
| **DELETE**       | /v1/posts/:id    | Deletes a blog post.                    | -                | **Authorization:** Token |
| **PATCH**        | /v1/posts/:id    | Updates a blog post.                    | *Fields in /v1/posts* | **Authorization:** Token<br>**Content-Type:** application/json |


# License
```
PyMock is a simple mock REST API written with Flask. Use if you need
a mock API in seconds.
Copyright (C) 2016  Halil Kaya

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```

[licence-badge]:http://img.shields.io/badge/licence-GPL-brightgreen.svg
