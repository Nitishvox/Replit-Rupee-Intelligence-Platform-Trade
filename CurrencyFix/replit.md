# RIPT - Rupee Intelligence Platform Trade

## Overview

RIPT (Rupee Intelligence Platform Trade) is a comprehensive Special Rupee Vostro Account (SRVA) management system built with Streamlit. The platform facilitates international trade settlements in Indian Rupees (INR) under the Reserve Bank of India's bilateral trade framework. RIPT serves as a complete end-to-end solution for banks and financial institutions to manage SRVA operations, process international transactions, ensure regulatory compliance, and provide advanced analytics for trade finance operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application providing a modern financial dashboard experience
- **Layout Design**: Wide responsive layout with expandable sidebar navigation optimized for financial operations
- **Visualization Engine**: Plotly Express and Plotly Graph Objects delivering interactive charts, real-time analytics, and financial reporting dashboards
- **Navigation Structure**: Tab-based modular interface separating functional areas (SRVA management, transaction processing, compliance tracking, reporting, document generation)
- **State Management**: Streamlit session state maintains persistent database connections and API instances across user interactions
- **Mobile Integration**: QR code generation and scanning capabilities for mobile payment processing and account management

### Backend Architecture
- **Modular Design**: Ten specialized business modules handling distinct operational areas:
  - **SRVAManager**: Complete SRVA account lifecycle management including creation, operations, and bulk processing
  - **TransactionProcessor**: International trade transaction handling with full lifecycle management from initiation to settlement
  - **SettlementCalculator**: Real-time INR settlement computations with live exchange rates and fee calculations
  - **ComplianceTracker**: Comprehensive RBI/FEMA compliance monitoring and automated regulatory reporting
  - **ReportingDashboard**: Advanced analytics engine providing business intelligence and operational metrics
  - **DocumentGenerator**: Automated generation of trade documents, compliance certificates, and official reports
  - **DataGenerator**: Sophisticated random data generation for testing, demonstration, and system validation
  - **QRCodeManager**: Mobile payment integration with secure QR code generation and scanning functionality
  - **EncryptionManager**: Multi-layer security with AES symmetric and RSA asymmetric encryption capabilities
  - **AIFraudDetector**: Machine learning-powered fraud detection using Isolation Forest and Random Forest algorithms
- **Security Architecture**: Enterprise-grade encryption with AES-256 for data at rest and RSA for secure key exchange
- **AI/ML Integration**: Advanced fraud detection using scikit-learn with anomaly detection and supervised classification models

### Data Storage
- **Primary Database**: SQLite with optimized normalized schema design for local data persistence and rapid deployment
- **Schema Structure**: Comprehensive tables covering SRVA accounts, transactions, exchange rates, compliance records, audit trails, and fraud detection datasets
- **Connection Management**: Context manager pattern ensuring proper database connection handling and ACID transaction integrity
- **Reference Data**: Structured JSON configuration files containing country data (20+ nations) and authorized bank information with SRVA capabilities
- **Caching Strategy**: Intelligent in-memory caching for exchange rates and frequently accessed reference data to optimize performance

### Authentication & Authorization
- **Current Implementation**: No authentication system (designed for secure internal banking environment)
- **Security Model**: Application assumes trusted network environment with network-level security controls and VPN access
- **Access Control**: Full functionality available to authenticated users (appropriate for internal banking operations)
- **Future Architecture**: Framework designed to support role-based access control for different user types (traders, compliance officers, administrators, auditors)

## External Dependencies

### Core Web Framework
- **Streamlit**: Primary web application framework providing rapid development and deployment capabilities
- **Pandas**: Data manipulation and analysis library for financial data processing
- **Plotly**: Interactive visualization library for charts, dashboards, and financial analytics

### Machine Learning & AI
- **scikit-learn**: Machine learning library powering fraud detection with Isolation Forest and Random Forest algorithms
- **NumPy**: Numerical computing foundation for mathematical operations and data analysis

### Security & Cryptography
- **cryptography**: Enterprise-grade encryption library providing AES and RSA encryption capabilities
- **base64**: Data encoding for secure transmission and storage

### Database & Data Management
- **SQLite3**: Embedded database engine for local data persistence and rapid deployment
- **JSON**: Configuration and reference data storage format

### Mobile & QR Integration
- **qrcode**: QR code generation library for mobile payment integration
- **Pillow (PIL)**: Image processing library for QR code manipulation and display
- **OpenCV (cv2)**: Computer vision library for QR code scanning and image processing

### External APIs
- **Exchange Rate Services**: Multiple free API providers for real-time currency conversion:
  - Fawaz Ahmed Currency API (CDN-hosted)
  - ExchangeRate.host (professional free tier)
  - ExchangeRate-API open access
- **Fallback System**: Comprehensive offline exchange rate data ensuring system resilience

### Development & Utilities
- **UUID**: Unique identifier generation for transactions and accounts
- **datetime**: Date and time handling for financial operations and audit trails
- **os**: Operating system interface for file and environment management
- **typing**: Type annotations for improved code quality and maintainability