---
title: "Deploying a Python App on Oracle Cloud Free Tier: A Step-by-Step Guide"
description: "Learn how to deploy a Python app on Oracle Cloud Free Tier with this comprehensive guide, covering setup, configuration, and deployment"
date: 2026-06-12
tags:
  - Python
  - Oracle Cloud
  - Cloud Computing
  - Free Tier
layout: post
---

## Introduction to Oracle Cloud Free Tier
Oracle Cloud Free Tier offers a free tier with generous limits, making it an attractive option for developers and businesses looking to deploy their applications in the cloud. With the Free Tier, you can deploy a Python app with ease, taking advantage of Oracle Cloud's robust infrastructure and scalable platform. In this article, we will walk you through the steps to deploy a Python app on Oracle Cloud Free Tier.
## Setting Up Your Oracle Cloud Account
To get started, you need to create an Oracle Cloud account. Go to the Oracle Cloud website and sign up for a free account. Fill out the registration form with your details, and verify your email address. Once you've verified your email, you'll be taken to the Oracle Cloud dashboard. From here, you can navigate to the Oracle Cloud Infrastructure (OCI) console, where you'll manage your resources and deploy your Python app.
### Creating a New Compartment
A compartment is a logical container that helps you organize your resources in Oracle Cloud. To create a new compartment, follow these steps: navigate to the OCI console, click on the 'Identity & Security' tab, and then click on 'Compartments'. Click the 'Create Compartment' button, enter a name and description for your compartment, and then click 'Create'.
## Installing the Oracle Cloud CLI
The Oracle Cloud CLI is a command-line tool that allows you to manage your Oracle Cloud resources from the comfort of your terminal. To install the Oracle Cloud CLI, follow these steps: download the Oracle Cloud CLI installer from the Oracle Cloud website, run the installer, and follow the prompts to install the CLI. Once installed, you'll need to configure the CLI by running the 'oci setup config' command and following the prompts to enter your Oracle Cloud credentials.
### Configuring the CLI
To configure the CLI, you'll need to enter your Oracle Cloud credentials, including your username, password, and tenant ID. You can find your tenant ID in the Oracle Cloud dashboard, under the 'Tenancy' section. Once you've entered your credentials, the CLI will configure itself and you'll be ready to start using it to manage your Oracle Cloud resources.
## Creating a New Virtual Machine
A virtual machine (VM) is a virtualized environment that runs on top of a physical server. To create a new VM, follow these steps: navigate to the OCI console, click on the 'Compute' tab, and then click on 'Instances'. Click the 'Create Instance' button, enter a name and description for your VM, and then select the 'Shape' (i.e., the size and type of VM) that best suits your needs. You'll also need to select an operating system image, such as Ubuntu or CentOS.
### Installing Python and Required Packages
Once your VM is up and running, you'll need to install Python and any required packages. You can do this by connecting to your VM using SSH and running the following commands: 'sudo apt-get update', 'sudo apt-get install python3', and 'sudo apt-get install python3-pip'. You'll also need to install any required packages, such as Flask or Django, using pip.
## Deploying Your Python App
To deploy your Python app, you'll need to copy your code to your VM and configure it to run. You can do this by using a tool like Git to clone your repository to your VM, and then running your app using a command like 'python3 app.py'. You'll also need to configure your app to listen on a specific port, such as port 80, and to handle incoming requests.
### Configuring the Firewall
To allow incoming traffic to your VM, you'll need to configure the firewall. You can do this by navigating to the OCI console, clicking on the 'Networking' tab, and then clicking on 'Virtual Cloud Networks'. Select the VCN that your VM is running in, and then click on the 'Security Lists' tab. Click the 'Create Security List' button, enter a name and description for your security list, and then add a rule to allow incoming traffic on the port that your app is listening on.
## Conclusion and Next Steps
In this article, we've walked you through the steps to deploy a Python app on Oracle Cloud Free Tier. By following these steps, you can take advantage of Oracle Cloud's robust infrastructure and scalable platform to deploy your Python app with ease. To get started, sign up for a free Oracle Cloud account today and start deploying your Python app. With Oracle Cloud Free Tier, you can deploy your app without incurring any costs, making it an attractive option for developers and businesses looking to get started with cloud computing. Don't wait – start deploying your Python app on Oracle Cloud Free Tier today and take the first step towards scalable and secure cloud-based application deployment.
