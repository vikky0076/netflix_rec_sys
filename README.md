# Netflix Movie Recommendation System

> A complete end-to-end **Content-Based Recommendation System** built with Python,
> TF-IDF Vectorization, and Cosine Similarity — runs entirely on CPU, no GPU required.

---

## 📁 Project Structure

```
Netflix_movie_recommendation_system/
│
├── dataset/
│   └── netflix_titles.csv        ← Place the Kaggle dataset here
│
├── recommendation.py             ← Core recommendation engine (run directly)
├── notebook.ipynb                ← Full interactive notebook with EDA & visualizations
├── requirements.txt              ← Python dependencies
└── README.md                     ← This file
```

---

## 📦 Dataset Download

This project uses the **Netflix Movies and TV Shows** dataset from Kaggle.

### Option A — Kaggle CLI (Recommended)

```bash
# 1. Install Kaggle
pip install kaggle

# 2. Download your API token from https://www.kaggle.com/account
#    (Account → API → "Create New Token" → downloads kaggle.json)

# 3. Place kaggle.json in the correct location:
#    Windows:  C:\Users\<YourUser>\.kaggle\kaggle.json
#    Linux/Mac: ~/.kaggle/kaggle.json

# 4. Download the dataset
kaggle datasets download -d shivamb/netflix-shows -p dataset/ --unzip
```

### Option B — Manual Download

1. Visit: [https://www.kaggle.com/datasets/shivamb/netflix-shows](https://www.kaggle.com/datasets/shivamb/netflix-shows)
2. Click **Download** (zip file)
3. Extract and place **`netflix_titles.csv`** inside the `dataset/` folder.

---

## 🚀 Installation

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Usage

### Run the recommendation script directly

```bash
python recommendation.py
```

This will output the **top 10 recommendations** for three sample movies:
- `Inception`
- `The Crown`
- `Money Heist`

### Use in your own Python code

```python
from recommendation import NetflixRecommender

# Initialize (loads and processes dataset once)
recommender = NetflixRecommender()

# Get recommendations
recommender.recommend("Stranger Things", top_n=10)
recommender.recommend("Breaking Bad", top_n=5)
```

### Run the Jupyter Notebook

```bash
jupyter notebook notebook.ipynb
```

The notebook includes:
- Full EDA with visualizations
- Genre distribution charts
- Release year trends
- Ratings distribution
- Live recommendation demos

---

## 🧠 How It Works

```
Netflix Dataset (8,807 titles)
         │
         ▼
  Data Cleaning
  (remove duplicates, fill NaN)
         │
         ▼
  Feature Engineering
  (combine: title + genre + description + director + cast)
         │
         ▼
  TF-IDF Vectorization
  (convert text → numerical vectors)
         │
         ▼
  Cosine Similarity Matrix
  (measure similarity between all movies)
         │
         ▼
  recommend_movies("Title", top_n=10)
  → Returns top 10 most similar titles
```

---

## 📚 Libraries Used

| Library       | Purpose                              |
|---------------|--------------------------------------|
| `pandas`      | Data loading and manipulation        |
| `numpy`       | Numerical operations                 |
| `matplotlib`  | Static visualizations                |
| `seaborn`     | Statistical visualizations           |
| `scikit-learn`| TF-IDF Vectorization, Cosine Similarity |

---

## ⚙️ System Requirements

- Python 3.8+
- No GPU required — runs entirely on CPU
- ~500 MB RAM for full TF-IDF matrix
- Any modern laptop

---

## 📄 License

This project is for **educational purposes** only. The dataset belongs to its respective owners on Kaggle.
