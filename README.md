# Mastering AWS IoT Core

[![Get it on Leanpub](https://img.shields.io/badge/Get_it_on-Leanpub-blue.svg)](https://leanpub.com/aws_iot_scale_fleet_management)
[![Available on Amazon](https://img.shields.io/badge/Available_on-Amazon-orange.svg)](#) <!-- Add your Amazon link here when live -->

Welcome to the official source code repository for **[Mastering AWS IoT Core: A Practical Guide to Connecting, Securing, and Managing IoT Devices at Scale](https://leanpub.com/aws_iot_scale_fleet_management)** by Jugurtha BELKALEM.

This repository contains all the accompanying source code and deployment scripts necessary to follow the practical labs and build the real-world scenarios detailed in the book.

## 📖 About the Book

Building an Internet of Things (***IoT***) ecosystem requires robust security, efficient telemetry routing, and scalable fleet management. *Mastering AWS IoT Core* is your comprehensive, hands-on guide to mastering the AWS IoT landscape. 

Whether you are a cloud architect, DevOps engineer, or IoT developer, this book takes you from absolute basics to production-ready deployments covering:
* **IoT Foundations:** Architectural patterns, MQTT protocols, and hardware selection.
* **Core Operations:** Bidirectional communication, state persistence (*Device Shadows*), the Rules Engine, and serverless compute via AWS Lambda.
* **Advanced Fleet Management:** Secure device provisioning at scale, Over-the-Air (***OTA***) updates, Edge computing with AWS IoT Greengrass, and enterprise-grade Zero Trust security.

## 📂 Repository Structure

The code is organized by chapter to help you easily locate the scripts and configurations as you read along:

```text
├── Chapter_03_Hardware_and_Material_Labs/   # Raspberry Pi & ESP32 baseline configurations
├── Chapter_05_Connecting_Your_First_Device/ # Python MQTT publishers and subscribers
├── Chapter_06_Managing_State_Persistence/   # Device Shadow interactions
├── Chapter_07_The_Rules_Engine/             # IoT SQL queries and routing logic
├── Chapter_08_Going_Serverless/             # AWS Lambda functions and SNS alerting
├── Chapter_09_Fleet_Provisioning/           # Bulk registration and template provisioning
├── Chapter_10_OTA_Updates/                  # AWS IoT Jobs and firmware update scripts
├── Chapter_11_Edge_Computing_Greengrass/    # Greengrass component deployments
└── Chapter_12_Security_Deep_Dive/           # Device Defender and secure tunneling setups
```

## 🤝 Contributing
Found a bug, a typo, or have a suggestion to improve the code? Please feel free to open an Issue or submit a Pull Request. Contributions are always welcome to keep this repository up-to-date with the latest AWS IoT best practices!

## ✍️ About the Author
**Jugurtha BELKALEM** is a **Tech Lead DevOps** and **IoT Engineer** specializing in embedded systems and scalable cloud infrastructure. Drawing on 8 years of professional experience, he focuses on designing resilient, secure architectures that bridge the gap between physical edge hardware and enterprise cloud environments. He actively orchestrates automated fleet provisioning, serverless compute integrations, and highly robust CI/CD pipelines.

LinkedIn: [https://www.linkedin.com/in/jugurtha-belkalem-707b7b105/](https://www.linkedin.com/in/jugurtha-belkalem-707b7b105/)

## 📄 License & Copyright
© 2026 Jugurtha BELKALEM. All rights reserved.

The content, text, and graphics associated with this book project are the intellectual property of the author. Code snippets provided within the companion repository are licensed under the MIT License.
