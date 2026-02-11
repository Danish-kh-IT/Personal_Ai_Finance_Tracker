# AI Finance Tracker

An intelligent expense tracking application built with Django that uses **Groq (Llama 3)** to automatically extract expense details from natural language input.

## Features

- 🤖 **AI-Powered Expense Extraction**: Describe your expense in natural language (e.g., "Spent 1200 on pizza"), and AI (Llama 3 via Groq) extracts item, amount, and category automatically.
- 📊 **Visual Dashboard**: Interactive charts showing spending breakdown by category and statistics.
- 📉 **Trend Analysis**: Daily and monthly spending trends with line and bar charts (last 30 days and 6 months).
- 💰 **Budget Management**: Set budgets for specific categories or overall spending with various periods (daily/weekly/monthly/yearly).
- ⚠️ **Budget Alerts**: Proactive notifications and visual warnings when budgets are exceeded or nearing limits.
- 📥 **Export Reports**: Download your entire expense history in **PDF, CSV, or MS Excel** formats.
- 🤖 **AI Financial Advice**: Get personalized savings tips based on your spending patterns.
- 📝 **Expense History**: View all your transactions in a clean, organized list with deletion support.
- 🔐 **User Authentication**: Secure signup and login functionality.
- 💾 **MySQL Database**: Robust data storage for reliable transaction management.
- ✨ **Premium UI**: Modern "Stitch" design with glassmorphism, dark mode support, and a custom branded favicon.

## Requirements

- Python 3.11+
- MySQL Server
- Groq Cloud API Key (for Llama 3)

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd AI_Finance_Tracker
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Create a `.env` file in the root directory
   - Add your Groq API key:
     ```env
     GROQ_API_KEY=your_groq_api_key_here
     ```

5. **Configure MySQL Database**
   - Create a database named `ai_finance_db`
   - Update database credentials in `core/settings.py` (USER, PASSWORD, HOST, PORT)

6. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Run the development server**

   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open browser and go to `http://127.0.0.1:8000`
   - Sign up for a new account or log in.

## Usage

1. **Add Expense**: Type your expense in simple English in the "Add Expense" box. AI handles the rest.
2. **Dashboard**: Monitor your "Financial Health" via real-time summary cards and charts.
3. **Get Advice**: Click "Get Advice" on the dashboard to receive a personalized AI savings tip.
4. **Reports**: Go to the **History** page and click **Download Report** to export your data in your desired format.
5. **Budgets**: Set spending limits to get alerted before you overspend.

## Technologies Used

- **Backend**: Django 5.2.10
- **Database**: MySQL
- **AI Engine**: Groq (Llama-3.3-70b-versatile)
- **Frontend**: Tailwind CSS, HTML5, JavaScript
- **Visualization**: Chart.js
- **PDF Generation**: xhtml2pdf
- **Excel Export**: openpyxl
- **Icons**: Lucide Icons

---

Developed with ❤️ for intelligent financial management.
