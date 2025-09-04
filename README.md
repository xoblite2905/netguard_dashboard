# Netguard: A Comprehensive Network Security Dashboard

> An all-in-one, containerized solution for live network traffic monitoring, threat detection, and security analysis, orchestrated with Docker and powered by the Elastic Stack.

This project provides a powerful and interactive dashboard to visualize network traffic, detect intrusions, and analyze security events in real-time. It leverages a suite of best-in-class open-source tools, all running seamlessly as Docker containers.

## ✨ Key Features

-   **Live Packet Analysis:** Captures and analyzes network traffic in real-time using Tshark, Zeek, and Suricata.
-   **Intrusion Detection System (IDS):** Utilizes Suricata for high-performance, rule-based threat and anomaly detection.
-   **Rich Traffic Logs:** Generates detailed and structured logs for various protocols (HTTP, DNS, SSL, etc.) using Zeek.
-   **Interactive Frontend:** A modern, responsive dashboard built with React to visualize alerts, network flows, and security metrics.
-   **Robust Backend:** Powered by a high-performance FastAPI backend to serve data to the frontend.
-   **Centralized Data Hub:** Aggregates logs and alerts from all services into Elasticsearch using Filebeat for powerful searching and analytics.
-   **Automated CI/CD:** Uses GitHub Actions to automatically build, test, and deploy the application, ensuring code quality and stability.

## 🛠️ Technology Stack

| Category               | Technologies                                        |
| ---------------------- | --------------------------------------------------- |
| **Orchestration**      | `Docker`, `Docker Compose`                          |
| **Backend**            | `Python`, `FastAPI`, `PostgreSQL`                   |
| **Frontend**           | `React`, `JavaScript`, `Tailwind CSS`               |
| **Data & Visualization** | `Elasticsearch`, `Kibana`, `Filebeat`               |
| **Network Analysis**   | `Suricata` (IDS), `Zeek` (NSM), `Tshark` (Packet Capture) |
| **CI/CD**              | `GitHub Actions`                                    |

## 🚀 Getting Started

Follow these instructions to set up and run the Netguard dashboard on your local machine.

### Prerequisites

-   [Git](https://git-scm.com/)
-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the Repository

First, clone the project from GitHub to your local machine.

```bash
git clone https://github.com/xoblite2905/netguard_dashboard.git
cd netguard_dashboard
