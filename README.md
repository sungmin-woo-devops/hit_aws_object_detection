https://labelstud.io/guide/storedata

---
```bash
(.venv) smallpod@orangepi5-plus:~/workspace/hit_aws_object_detection/infra$ ./start.sh 
🚀 MinIO + Label Studio 서비스를 시작합니다...
📋 환경 변수를 로드합니다...
🐳 Docker Compose로 서비스를 시작합니다...
Creating network "infra_default" with the default driver
Creating infra_prometheus_1 ... done
Creating infra_minio_1      ... done
⏳ 서비스가 시작되는 동안 잠시 기다립니다...
🔍 서비스 상태를 확인합니다...
       Name                     Command               State                                          Ports                                        
--------------------------------------------------------------------------------------------------------------------------------------------------
infra_minio_1        /usr/bin/docker-entrypoint ...   Up      0.0.0.0:19000->9000/tcp,:::19000->9000/tcp, 0.0.0.0:9001->9001/tcp,:::9001->9001/tcp
infra_prometheus_1   /bin/prometheus --config.f ...   Up      9090/tcp                                                                            
✅ 서비스가 시작되었습니다!

📋 접속 정보:
  - MinIO API: http://localhost:19000
  - MinIO Console: http://localhost:9001
  - Label Studio: http://localhost:8080

🔧 관리 명령어:
  - 서비스 중지: ./stop.sh
  - 로그 확인: docker-compose -f compose.minio.yml logs -f
(.venv) smallpod@orangepi5-plus:~/workspace/hit_aws_object_detection/infra$ docker ps
CONTAINER ID   IMAGE                                      COMMAND                   CREATED              STATUS                PORTS                                                                                        NAMES
030b1071f951   minio/minio:RELEASE.2025-04-22T22-12-26Z   "/usr/bin/docker-ent…"   About a minute ago   Up About a minute     0.0.0.0:9001->9001/tcp, [::]:9001->9001/tcp, 0.0.0.0:19000->9000/tcp, [::]:19000->9000/tcp   infra_minio_1
c28b0c2271b8   quay.io/prometheus/prometheus:v2.37.1      "/bin/prometheus --c…"   About a minute ago   Up About a minute     9090/tcp                                                                                     infra_prometheus_1
888ad787c9b4   adminer                                    "entrypoint.sh docke…"   8 days ago           Up 8 days             0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp                                                  adminer
48df064142d8   mariadb:10.6.22-ubi9                       "docker-entrypoint.s…"   8 days ago           Up 8 days (healthy)   0.0.0.0:3306->3306/tcp, [::]:3306->3306/tcp                                                  mariadb
33c7c8da6fcf   moby/buildkit:buildx-stable-1              "buildkitd --allow-i…"   7 months ago         Up 8 days                                                                                                          buildx_buildkit_custom_builder0
(.venv) smallpod@orangepi5-plus:~/workspace/hit_aws_object_detection/infra$ docker compose ps
NAME                 IMAGE                                      COMMAND                   SERVICE      CREATED              STATUS              PORTS
infra_minio_1        minio/minio:RELEASE.2025-04-22T22-12-26Z   "/usr/bin/docker-ent…"   minio        About a minute ago   Up About a minute   0.0.0.0:9001->9001/tcp, [::]:9001->9001/tcp, 0.0.0.0:19000->9000/tcp, [::]:19000->9000/tcp
infra_prometheus_1   quay.io/prometheus/prometheus:v2.37.1      "/bin/prometheus --c…"   prometheus   About a minute ago   Up About a minute   9090/tcp
```