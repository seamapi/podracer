import json
import os

from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

MANIFEST_V2_TYPE = 'application/vnd.docker.distribution.manifest.v2+json'
MANIFEST_LIST_TYPE = 'application/vnd.docker.distribution.manifest.list.v2+json'
IMAGE_TYPE = 'application/vnd.docker.container.image.v1+json'

DOCKERHUB_ALIASES = ['docker.io', 'registry-1.docker.io', 'https://index.docker.io/v1/']


def qualify_image(image):
  if len(image.split('/')) < 2:
    image = 'library/' + image

  if len(image.split('/')) < 3:
    image = 'registry-1.docker.io/' + image

  if len(image.split(':')) < 2:
    image += ':latest'

  return image


def find_credentials(registry, auth):
  if 'auths' not in auth:
    return None

  if registry in auth['auths']:
    return auth['auths'][registry]['auth']
  elif registry in DOCKERHUB_ALIASES:
    for alias in DOCKERHUB_ALIASES:
      if alias in auth['auths']:
        return auth['auths'][alias]['auth']

  return None


def registry_credentials(registry):
  # See if we've logged in with podman or skopeo
  if 'XDG_RUNTIME_DIR' in os.environ:
    containers_auth = Path(os.environ['XDG_RUNTIME_DIR']).joinpath(f"{os.getuid()}/containers/auth/json")
    if containers_auth.exists():
      with open(containers_auth) as io:
        credentials = find_credentials(registry, json.load(io))
        if credentials is not None:
          return credentials

  # See if we've logged in with docker
  docker_auth = Path.home().joinpath('.docker/config.json')
  if docker_auth.exists():
    with open(docker_auth) as io:
      credentials = find_credentials(registry, json.load(io))
      if credentials is not None:
        return credentials

  # Sorry, no creds :(
  return None


def registry_request(url, headers={}, token=None, method='GET'):
  try:
    if token is not None:
      headers['Authorization'] = f"Bearer {token}"

    response = urlopen(Request(url, headers=headers, method=method))
    setattr(response, 'token', token)

    return response
  except HTTPError as error:
    if (error.code != 401) or (token is not None):
      raise

    auth_header = error.headers['Www-Authenticate']
    auth_type, fields = auth_header.split(None, 1)

    if auth_type != 'Bearer':
      raise RuntimeError(f"Don't know how to handle '{auth_type}' auth")

    realm = None
    params = []

    for field in fields.split(','):
      key, value = field.split('=', 1)
      value = value.strip('"')

      if key == 'realm':
        realm = value
      else:
        params.append(f"{key}={value}")

    if realm is None:
      raise RuntimeError("No realm in Www-Authenticate header")

    auth_headers = {}
    credentials = registry_credentials(urlparse(url).netloc)
    if credentials is not None:
      auth_headers = {'Authorization': f"Basic {credentials}"}

    response = urlopen(Request(realm + '?' + '&'.join(params), headers=auth_headers))
    auth = json.load(response)
    response.close()

    if 'token' not in auth:
      raise RuntimeError("No token in response")

    return registry_request(url, headers, auth['token'], method)


def get_manifests(image):
  image = qualify_image(image)
  base_url, image = image.split('/', 1)
  repository, tag = image.split(':', 1)

  if base_url in DOCKERHUB_ALIASES:
    base_url = 'registry-1.docker.io'

  url = f"https://{base_url}/v2/{repository}/manifests/{tag}"
  headers = {"Accept": f"{MANIFEST_LIST_TYPE}, {MANIFEST_V2_TYPE}"}

  response = registry_request(url, headers)
  body = json.load(response)
  response.close()

  content_type = response.headers['Content-Type']

  if content_type == MANIFEST_LIST_TYPE:
    # manifest lists are easy and need no further processing
    return body['manifests']
  elif content_type == MANIFEST_V2_TYPE:
    # ugh, we have to actually fetch the image
    if body['config']['mediaType'] != IMAGE_TYPE:
      raise RuntimeError(f"Unknown mediaType: {body['config']['mediaType']}")

    manifest = {'digest': response.headers['Docker-Content-Digest']}

    url = f"https://{base_url}/v2/{repository}/blobs/{body['config']['digest']}"
    headers = {"Accept": IMAGE_TYPE}

    response = registry_request(url, headers, response.token)
    body = json.load(response)
    response.close()

    manifest['platform'] = {'architecture': body['architecture'], 'os': body['os']}
    if 'variant' in body:
      manifest['platform']['variant'] = body['variant']

    return [manifest]
  else:
    # who knows what this is?
    raise RuntimeError(f"Unknown content type: {content_type}")
