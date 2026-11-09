# TaskFlow — INFAL198 Technologies DevOps

API de départ pour les ateliers. Depuis votre fork, installez Python 3.12 et créez un environnement virtuel avec `python -m venv .venv`. Activez-le sous Linux avec `source .venv/bin/activate` ou sous PowerShell avec `.\.venv\Scripts\Activate.ps1`.

    python -m pip install -r requirements.txt
    ruff check .
    python -m pytest -q
    python -m flask --app app run --port 8000

Ouvrez http://127.0.0.1:8000/health puis /metrics. GET /tasks liste les tâches. POST /tasks accepte un corps JSON tel que {"title":"Tester le pipeline"} et renvoie 201. Depuis PowerShell :

    Invoke-RestMethod http://localhost:8000/tasks -Method Post -ContentType application/json -Body '{"title":"Tester le pipeline"}'

## Parcours

1. **CI** — Créez .github/workflows/ci.yml d’après la diapo 19. Nommez le job test. Faites-le tourner une fois avant de le sélectionner comme vérification obligatoire sur main. Cassez le test de santé sur une branche puis corrigez-le dans la même pull request.
2. **Terraform et Ansible** — Créez main.tf, inventory.ini et site.yml à la racine. Le modèle templates/index.html.j2 est fourni. Vérifiez le résultat puis rejouez le playbook.
3. **Conteneurs** — Écrivez le Dockerfile à la racine. Le point d’entrée Gunicorn est app:app, avec un seul worker et une écoute sur 0.0.0.0:8000. Testez l’image puis créez le Deployment et le Service. Définissez APP_VERSION=v2 dans la deuxième image pour identifier la version via /health.
4. **Observabilité** — Appelez /health pour initialiser la série. L’histogramme http_request_duration_seconds porte les labels route et status et inclut la borne 0.3. Avec kind, utilisez le Service depuis un pod client et comparez les mesures client et serveur pendant la suppression d’un seul pod. En solution de repli, une fois le Dockerfile de l’atelier 3 créé, exécutez depuis la racine docker compose -f observabilite/compose.yaml up --build. Prometheus est disponible sur localhost:9090 et Grafana sur localhost:3000. Ce repli permet l’observation locale ; l’expérience à trois réplicas se déroule sur kind. Pour arrêter : docker compose -f observabilite/compose.yaml down.
5. **Atelier 5 en ++** — Déployez l’image chez le fournisseur choisi. Configurez le port cible 8000 puis vérifiez /health.

SQLite utilise un fichier local par instance. Les tâches de démonstration peuvent disparaître au remplacement du conteneur et chaque réplica a sa propre liste. Utilisez /health pour l’expérience de disponibilité. Pour disposer d’une liste commune durable, il faudrait une base partagée.

## Atelier 2 — commandes

Prérequis : Docker démarré, Terraform ≥ 1.6 et `python -m pip install ansible docker` (le paquet `ansible` inclut la collection `community.docker`).

    terraform init
    terraform apply            # crée taskflow-web-1 et taskflow-web-2 (ports 8081 et 8082)
    ansible-playbook -i inventory.ini site.yml   # 1er passage : changed=1 par hôte
    curl http://127.0.0.1:8081                   # <h1>taskflow-web-1</h1>
    ansible-playbook -i inventory.ini site.yml   # 2e passage : changed=0 (idempotent)
    terraform destroy

## Atelier 3 — commandes

    docker build -t taskflow:v1 .
    docker run --rm -p 8000:8000 taskflow:v1        # http://127.0.0.1:8000/health → "version": "v1"
    docker build --build-arg APP_VERSION=v2 -t taskflow:v2 .

    kind create cluster --name taskflow
    kind load docker-image taskflow:v1 taskflow:v2 --name taskflow
    kubectl apply -f k8s/
    kubectl rollout status deployment/taskflow
    kubectl run client --rm -it --image=curlimages/curl --restart=Never -- curl -s http://taskflow/health
    kubectl set image deployment/taskflow taskflow=taskflow:v2   # passage en v2
    kubectl run client --rm -it --image=curlimages/curl --restart=Never -- curl -s http://taskflow/health
