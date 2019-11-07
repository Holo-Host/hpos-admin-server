# hpos-admin-server
Authenticate Admin access and serve administrative REST APIs

## Building and Installing

Run `make install` to build and install the `hpos-admin-server` Python3 module locally.


## Testing

After installation of `hpos-admin-server`, you can run it, providing a test directory containing
testing `data/holo-config.json` as well as `templates/` and `static/` directories to serve
`text/html` responses to a browser.  This increases verbosity, and runs the web server in "debug"
mode, producing verbose `text/html` stack traces:

```
python3 -m hpos-admin-server -dvv -C ~/src/hpos-admin-server/test
http://localhost:5555/
127.0.0.1:52949 - - [06/Nov/2019 13:59:29] "HTTP/1.1 GET /api/v1/config" - 200 OK
```

### Testing with `curl`

Hit the `hpos-admin-server` with `curl` to see `application/json` responses, by default:

```
$ curl localhost:5555/api/v1/config
{
    "admin": {
        "email": "a@b.ca",
        "public_key": "baByq+hINRWCV3mn5uEtFxsNMDtrsTc+Qe64Evju/PQ"
    }
} $
```

## Production

To run the `hpos-admin-server` in production (and without support for HTTP `text/html` responses to
support browser clients), all that is required is a `data/` directory in the current directory (or,
optionally, in the directory supplied via `-C <directory>`.  

```
$ python3 -m hpos-admin-server
http://localhost:5555/
...
```

### The `data/` Directory

All local production data required by the `hpos-admin-server` must be in the `./data/` directory.

- `holo-config.json`
  - A symbolic link (or copy) of this file is required to serve `api/v#/config`.  The `seed` is of
    course not revealed.
- `run/{current, booted}-system`
  - A symbolic link to NixOS's /run/ (or, to the individual ...-system paths required)
