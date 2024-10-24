# Collection Monitorr
Make sure your Radarr collections are always monitored!

## Running in Docker

### Docker run
```
docker run -d \
    -e RADARR_API_KEY=<API Key For Radarr> \
    -e RADARR_URL=<URL to access Radarr> \
    -e REFRESH_MINUTES=<Minutes between refreshes, default 10>
    --name collection-monitorr \
    ghcr.io/diamkil/collection-monitorrr:main
```

### Docker-Compose
```
services:
  collection-monitorr:
    image: ghcr.io/diamkil/collection-monitorrr:main
    container_name: collection-monitorr
    environment:
      - RADARR_API_KEY=<API Key For Radarr>
      - RADARR_URL=<URL to access Radarr>
      - REFRESH_MINUTES=<Minutes between refreshes, default 10>
```
