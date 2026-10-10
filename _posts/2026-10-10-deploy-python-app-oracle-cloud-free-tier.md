---
title: "How to Deploy a Python App on Oracle Cloud Free Tier"
description: "Deploy a Python web app on Oracle Cloud Free Tier in minutes. Step‑by‑step guide, tools, and best practices for beginners."
date: 2026-10-10
tags:
  - Python
  - Oracle Cloud
  - Free Tier
  - Deployment
  - Cloud Computing
layout: post
---

## What the Oracle Cloud Free Tier Offers for Python
Oracle Cloud’s Free Tier gives you access to a small virtual machine, storage, and networking for free, as long as you stay within the limits. The free compute instance runs Ubuntu 22.04 LTS, which is fully compatible with Python 3.10+. You also get a free block volume, a load balancer, and a DNS zone, all of which are useful when you want a production‑ready deployment without paying a dime. The main trade‑off is that the instance is limited to one CPU core and 1 GB of RAM, so keep your app lightweight or use a micro‑service architecture.

## Prepare Your Local Development Environment
1. **Install Python** – Download the latest Python 3.10 from python.org or use a package manager like `apt` on Ubuntu. Verify with `python3 --version`.
2. **Create a virtual environment** – Run `python3 -m venv venv` and activate it with `source venv/bin/activate`. This keeps dependencies isolated.
3. **Write a minimal Flask app** – Create `app.py`:
   ```python
   from flask import Flask
   app = Flask(__name__)
   @app.route('/')
   def hello():
       return 'Hello from Oracle Cloud!'
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000)
   ```
4. **Test locally** – Run `python app.py` and open `http://localhost:5000`. If you see the greeting, your code is ready.
5. **Pin dependencies** – Use `pip freeze > requirements.txt` so the server can install the same versions.

## Create an Oracle Cloud Compute Instance
1. Sign in to the Oracle Cloud console.
2. Click **Compute** → **Instances** → **Create Instance**.
3. Name the instance and choose the **Canonical Ubuntu 22.04 LTS** image.
4. In the **Shape** section, pick **VM.Standard.E2.1.Micro** (Free Tier eligible). This gives 1 CPU and 1 GB RAM.
5. Under **Networking**, select the default VCN or create a new one. Keep the public IP enabled so you can SSH.
6. Add a **Free Tier** **SSH key** – paste your public key from `~/.ssh/id_rsa.pub`.
7. Review and create. The instance will appear in the list after a few minutes.

## Set Up the Server for Python
SSH into the instance:
```bash
ssh -i ~/.ssh/id_rsa opc@<public‑IP>
```
Once logged in, run:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
```
Create a directory for the app:
```bash
mkdir ~/myapp && cd ~/myapp
```
Transfer the files from your local machine using `scp` or `git clone` if you have a repo:
```bash
scp -i ~/.ssh/id_rsa app.py requirements.txt opc@<public‑IP>:~/myapp/
```
Set up a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Deploy Your App with Docker or Native
### Option 1: Native Deployment
Run the Flask app directly:
```bash
python app.py
```
For production, use **Gunicorn**:
```bash
pip install gunicorn
gunicorn -b 0.0.0.0:5000 app:app
```
### Option 2: Docker Deployment
Create a `Dockerfile`:
```docker
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```
Build and run:
```bash
docker build -t myapp .
docker run -d -p 5000:5000 myapp
```
#### Comparison Table
| Feature | Native (Gunicorn) | Docker | Trade‑off |
|---------|-------------------|--------|-----------|
| Startup time | ~5 s | ~10 s | Docker adds a layer |
| Port exposure | 5000 | 5000 | Same |
| Portability | Limited to Ubuntu | Portable across OS | Docker is easier to move |
| Resource usage | Slightly lower | Higher overhead | Docker consumes ~50 MB more RAM |

## Configure Networking and DNS
1. **Open port 5000** – In the console, go to **Networking** → **Security Lists** and add an ingress rule for TCP port 5000 from 0.0.0.0/0.
2. **Configure Nginx as a reverse proxy** – Edit `/etc/nginx/sites-available/default`:
   ```nginx
   server {
       listen 80;
       server_name _;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   Reload Nginx: `sudo systemctl reload nginx`.
3. **Set up a DNS record** – In Oracle Cloud DNS, create an **A** record pointing your domain to the instance’s public IP. If you don’t own a domain, use a free DNS service like Cloudflare to create a subdomain.

## Monitor, Scale, and Clean Up
- **Logging** – Tail the Nginx logs with `sudo tail -f /var/log/nginx/access.log` and error logs with `sudo tail -f /var/log/nginx/error.log`.
- **Health checks** – Use the built‑in Oracle Cloud load balancer health check or a simple script that pings `http://localhost:5000`.
- **Scaling** – The Free Tier does not support auto‑scaling. If traffic grows, you’ll need to upgrade to a paid shape or split the app into micro‑services.
- **Cost control** – Disable the instance when not in use: `sudo shutdown -h now` and stop the instance from the console. Remember that the free block volume persists; delete it if you’re done: **Block Storage** → **Volumes** → **Delete**.

## Common Pitfalls and How to Avoid Them
| Issue | Symptom | Fix |
|-------|---------|-----|
| SSH key not accepted | “Permission denied (publickey)” | Ensure the public key is in the correct format and that the instance uses the `opc` user. |
| App not reachable | Browser shows *Connection timed out* | Verify the security list allows port 5000 and that Nginx is running. |
| Memory exhaustion | `Killed` message after a few requests | Reduce the app’s memory footprint or switch to a paid VM with more RAM. |
| DNS not resolving | “Domain not found” | Check that the A record points to the correct IP and that DNS propagation has completed. |

## Official references
- Oracle Cloud Free Tier Overview: https://www.oracle.com/cloud/free/
- Python 3.10 Release Notes: https://www.python.org/downloads/release/python-3100/

## Takeaway
Deploying a Python app on Oracle Cloud Free Tier is straightforward: spin up a small Ubuntu VM, install Python and your dependencies, and expose the app via Nginx or Docker. The free tier is perfect for prototypes, learning, or low‑traffic services. Next, experiment with adding a database like MySQL or PostgreSQL from the free tier catalog and connect it to your app. This will give you a full‑stack experience and prepare you for scaling when your traffic grows.
