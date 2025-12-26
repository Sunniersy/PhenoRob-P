# PhenoRob-P: An Autonomous Robotic System for High-Throughput Phenotyping of Potted Plants

**PhenoRob-P** is an integrated intelligent platform designed for high-throughput crop phenomics in facility agriculture (greenhouses, polytunnels). By integrating a "Perception-Localization-Execution-Analysis" closed-loop pipeline, it overcomes core challenges such as narrow-aisle navigation, GNSS-denied environments, and high-precision data acquisition under complex canopies.

------

## 🚀 Key Highlights

- **High Mobility**: Features a two-wheel differential drive with **zero turning radius**, specifically optimized for narrow aisles (width $< 60\text{cm}$).
- **LiDAR-Vision Fusion**: Achieves sub-**$30\text{mm}$** repetitive localization precision in GNSS-denied indoor environments.
- **Adaptive Pose Compensation**: Utilizes **Inverse Kinematics (IK)** algorithms to maintain dynamic alignment between the 6-DOF robotic arm and plants.
- **Edge-Cloud Collaboration**: A "User-Cloud-Robot" architecture using MQTT/FTP for efficient data transmission and automated phenotyping analysis.

------

## 🏗️ System Architecture

The system is built on a distributed three-tier framework to ensure scalability and reliability:

1. **Hardware Execution Layer**: Includes the differential suspension chassis, NVIDIA Jetson edge core, and the 6-DOF robotic arm.
2. **Perception & Control Layer**: Runs SLAM navigation, YOLOv11-based pot identification, OCR ID matching, and robotic arm pose compensation.
3. **Cloud Management Layer**: Handles data storage (FTP), task scheduling (MQTT), and real-time status monitoring (WebSocket).

------

## 🛠 Hardware Specifications

| **Module**             | **Key Components**                     | **Technical Parameters**                                    |
| ---------------------- | -------------------------------------- | ----------------------------------------------------------- |
| **Mobile Chassis**     | Custom Differential Drive + Suspension | $65 \times 50 \times 30 \text{cm}$, Payload $> 20\text{kg}$ |
| **Computing Unit**     | NVIDIA Jetson Orin Nano                | 40 TOPS AI Performance, 8GB LPDDR5                          |
| **Navigation Sensors** | Oradar MS500 LiDAR + D435i             | 2D Laser Ranging + Side-view Depth Vision                   |
| **Phenotyping Unit**   | Azure Kinect DK + RM65-B Arm           | 4K RGB + High-res Point Cloud, 6-DOF                        |
| **Power System**       | 24V 30Ah LiFePO4 Battery               | 4–6 hours of continuous operation                           |

------

## 🧠 Core Algorithms

### 1. Coordinate Transformation & Localization

The system detects the pot via the side-view camera and maps the local coordinates $P_{camera}$ to the robot's global base frame $P_{base}$ using a homogeneous transformation matrix:

$$\begin{bmatrix} X_{base} \\ Y_{base} \\ Z_{base} \\ 1 \end{bmatrix} = \begin{bmatrix} R_{3 \times 3} & T_{3 \times 1} \\ 0 & 1 \end{bmatrix} \cdot \begin{bmatrix} X_{camera} \\ Y_{camera} \\ Z_{camera} \\ 1 \end{bmatrix}$$

Where $R$ and $T$ represent the rotation matrix and translation vector of the camera relative to the chassis.

### 2. Real-time Robotic Arm Compensation

To counter minor deviations during movement, the system solves inverse kinematics equations analytically to adjust the 6 joint angles $\theta_n$ at a frequency of **100Hz**, ensuring the sensor remains focused on the plant canopy.

------

## 📈 Performance & Validation

### 1. Acquisition Efficiency

| **Mode**                  | **Efficiency (Pots/Hour)** | **Target Scenario**                              |
| ------------------------- | -------------------------- | ------------------------------------------------ |
| **Continuous Scanning**   | ~520                       | Rapid population screening, large-scale coverage |
| **Multi-angle Fine Mode** | ~187                       | 3D reconstruction, organ-level extraction        |

### 2. Navigation Accuracy

| **Speed**         | **Longitudinal Error (Mean)** | **Lateral Error (Mean)** |
| ----------------- | ----------------------------- | ------------------------ |
| $0.2 \text{ m/s}$ | $15.6 \text{ mm}$             | $10.5 \text{ mm}$        |
| $0.3 \text{ m/s}$ | $23.8 \text{ mm}$             | $11.1 \text{ mm}$        |

### 3. Biological Accuracy

Validated through experiments on Maize and Wheat:

- **Maize Plant Height**: $R^2 = 0.940$
- **Maize Stem Diameter**: $R^2 = 0.845$
- **Environmental Robustness**: Successfully quantified the dynamic evolution of **Leaf Yellow-Green Ratio (YGR)** in wheat under drought stress and re-watering phases.
