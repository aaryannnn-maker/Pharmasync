# PharmaSync

**PharmaSync** is a production-ready **Pharmacy Inventory Management & Analytics System** built using **Python and Flask**. It is designed to handle real-world pharmacy operations including inventory tracking, sales processing, supplier procurement, and financial reporting with clear debit–credit accounting logic.

PharmaSync focuses on **accuracy, auditability, and operational efficiency**, making it suitable for academic projects, small pharmacies, or as a foundation for enterprise-scale systems.

---

## Overview

PharmaSync centralizes all pharmacy operations into a single system:

* Real-time medicine stock visibility
* Automated inventory updates during sales and purchases
* Clear financial insights using debit–credit principles
* Printable PDF reports for accounting and audits

The system is built with **data integrity and simplicity** as core principles.

---

## Key Features

* **Dashboard Analytics**
  View total medicines, low-stock alerts, and expired items at a glance.

* **Inventory Control**
  Track medicines by category, batch number, quantity, and expiry date.

* **Sales Management**
  Process customer sales with automatic stock deduction and revenue logging.

* **Supplier & Procurement Management**
  Create and manage purchase orders with supplier linkage.

* **Financial Reporting**
  Date-wise revenue, expense, and net profit calculations.

* **PDF Report Export**
  Generate professional, printable financial reports using pure Python tools.

---

## System Modules

### Inventory Management

* Add, update, and monitor medicines
* Automatic alerts for low-stock and near-expiry items
* Prevents overselling by validating stock availability

---

### Sales Module (Credit Transactions)

* Records customer sales
* Calculates total amount based on unit price × quantity
* Updates inventory in real time
* Generates **Credit** entries in financial records

---

### Supplier & Purchase Orders (Debit Transactions)

* Maintain supplier information
* Create purchase orders
* Upon order completion:

  * Stock is added to inventory
  * Expense is recorded as a **Debit** entry

---

## Accounting Logic

PharmaSync uses a simplified accounting model aligned with standard business practices:

| Transaction Type | Description      | Financial Impact  |
| ---------------- | ---------------- | ----------------- |
| **Credit**       | Customer Sales   | Increases Revenue |
| **Debit**        | Purchase Orders  | Increases Expense |
| **Net Balance**  | Credits − Debits | Profit or Loss    |

This approach provides transparent and audit-friendly financial reporting.

---

## Technology Stack

* **Language:** Python 3.12+
* **Framework:** Flask
* **ORM:** SQLAlchemy (SQLite)
* **Authentication:** Flask-Login
* **Frontend:** Tailwind CSS
* **PDF Engine:** xhtml2pdf

---

## Project Structure

```text
pharmasync/
│── app.py
│── models.py
│── routes/
│   ├── inventory.py
│   ├── sales.py
│   ├── suppliers.py
│   └── reports.py
│── templates/
│── static/
│── instance/
│   └── database.db
│── requirements.txt
│── README.md
```

---

## Installation & Setup

###  Clone the Repository

```bash
git clone https://github.com/yourusername/pharmasync.git
cd pharmasync
```

---

###  Create & Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

---

###  Install Dependencies

```bash
pip install -r requirements.txt
```

---

###  Initialize Database

```bash
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

---

###  Run the Application

```bash
python app.py
```

Access the application at:

```
http://127.0.0.1:5000
```

---

## 🗄 Database Design

| Table             | Description                   |
| ----------------- | ----------------------------- |
| **User**          | Authenticated pharmacy staff  |
| **Medicine**      | Medicine details & stock      |
| **Sale**          | Records of customer purchases |
| **Supplier**      | Distributor information       |
| **PurchaseOrder** | Procurement and expenses      |

Foreign key relationships ensure data consistency across transactions.

---

## Reports & PDF Generation

* Financial reports generated from HTML templates
* Converted to PDF using **xhtml2pdf**
* No external binaries required
* Optimized for printing and auditing

---

## Future Enhancements

* Role-based access control (Admin / Staff)
* REST API for mobile or POS integration
* Barcode scanning support
* Cloud database support (PostgreSQL)
* Automated email reports

---

© 2026 **PharmaSync Systems**
Built with precision. Designed for reliability.
