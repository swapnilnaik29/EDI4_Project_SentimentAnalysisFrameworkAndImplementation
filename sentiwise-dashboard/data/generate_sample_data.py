import csv
import random
import uuid
from datetime import datetime, timedelta

NUM_REVIEWS = 500

business_units = ["Banking", "Telecom", "SaaS", "E-commerce", "Food Delivery"]

products_services = {
    "Banking": ["Checking Account", "Credit Card", "Mortgage", "Personal Loan", "Mobile App"],
    "Telecom": ["5G Data Plan", "Fiber Internet", "Customer Support", "Device Upgrade"],
    "SaaS": ["CRM Dashboard", "API Access", "Billing System", "Analytics Module"],
    "E-commerce": ["Electronics", "Apparel", "Home Goods", "Shipping & Delivery"],
    "Food Delivery": ["Late Night Menu", "Grocery Delivery", "Restaurant Partner", "Subscription Pass"]
}

reviewer_types = ["Verified Buyer", "Anonymous", "Guest", "Subscriber"]
reviewer_names = ["John D.", "Alice S.", "Bob M.",
                  "Charlie R.", "Diana P.", "Eve K.", "Frank T.", "Grace H."]
platforms = ["Web", "iOS App", "Android App", "In-Store Kiosk", "Email"]
device_types = ["Desktop", "Mobile", "Tablet"]
purchase_types = ["One-time", "Subscription", "Renewal", "Upgrade"]
customer_tiers = ["Standard", "Premium", "VIP", "Enterprise"]
languages = ["en"]
locations = [
    {"city": "New York", "state": "NY", "country": "USA"},
    {"city": "San Francisco", "state": "CA", "country": "USA"},
    {"city": "Austin", "state": "TX", "country": "USA"},
    {"city": "London", "state": "ENG", "country": "UK"},
    {"city": "Toronto", "state": "ON", "country": "Canada"},
    {"city": "Sydney", "state": "NSW", "country": "Australia"}
]

# Text templates based on sentiment and business unit
positive_templates = [
    "I absolutely love the {product}. The {aspect} is fantastic and highly recommended!",
    "Great experience with {product}. The {aspect} made it totally worth it.",
    "Outstanding {aspect}! I've been using the {product} for months and couldn't be happier.",
    "Five stars. The {product} exceeded my expectations, especially the {aspect}."
]

negative_templates = [
    "Terrible {aspect}. The {product} is a complete waste of money.",
    "I had a horrible experience with the {product}. The {aspect} broke immediately.",
    "Very disappointed in the {product}. {aspect} is unacceptable. Fix this ASAP!",
    "The {product} is buggy. The {aspect} never works right. I want a refund."
]

mixed_templates = [
    "The {product} is okay. The {aspect} is good, but the other features are lacking.",
    "While the {aspect} of the {product} is decent, the overall experience was frustrating.",
    "I like the {product}, but the {aspect} needs a lot of improvement.",
    "Decent {product}, however the {aspect} is extremely slow."
]

sarcastic_templates = [
    "Oh brilliant, another update that breaks the {product}. Masterful {aspect} work.",
    "Wow, I just love waiting 45 minutes for the {product}. Amazing {aspect}!",
    "Sure, charge me double for the {product}. Best {aspect} ever. Not."
]

toxic_templates = [
    "This {product} is absolute garbage. The developers who made this {aspect} are idiots.",
    "Non sense {product} and the stupid {aspect}. I hate this company.",
    "Worst {product} ever. You people are scammers with your trash {aspect}."
]

aspects = {
    "Banking": ["interest rate", "app interface", "customer service", "fraud detection"],
    "Telecom": ["connection speed", "coverage", "router setup", "billing"],
    "SaaS": ["uptime", "UI/UX", "API documentation", "data export"],
    "E-commerce": ["shipping speed", "packaging", "return policy", "checkout process"],
    "Food Delivery": ["food temperature", "delivery driver", "app tracking", "menu variety"]
}


def generate_review_text(bu, product, sentiment):
    aspect = random.choice(aspects[bu])
    if sentiment == "Positive":
        template = random.choice(positive_templates)
    elif sentiment == "Negative":
        template = random.choice(negative_templates)
    elif sentiment == "Mixed":
        template = random.choice(mixed_templates)
    elif sentiment == "Sarcastic":
        template = random.choice(sarcastic_templates)
    elif sentiment == "Toxic":
        template = random.choice(toxic_templates)

    return template.format(product=product, aspect=aspect)


def map_sentiment_to_rating(sentiment):
    if sentiment == "Positive":
        return random.randint(4, 5)
    elif sentiment in ["Negative", "Toxic", "Sarcastic"]:
        return random.randint(1, 2)
    else:
        return random.randint(2, 4)


def generate_dataset(filename="reviews_dataset.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = [
            "review_id", "review_text", "reviewer_type", "reviewer_name",
            "business_unit", "product_or_service", "rating", "location",
            "city", "state", "country", "timestamp", "date", "platform",
            "device_type", "sentiment_label", "purchase_type", "customer_tier",
            "response_time", "resolved", "language", "transaction_amount", "tags"
        ]
        writer.writerow(header)

        start_date = datetime.now() - timedelta(days=365)

        sentiments = ["Positive", "Negative", "Mixed", "Sarcastic", "Toxic"]
        sentiment_weights = [0.4, 0.3, 0.15, 0.1, 0.05]

        for _ in range(NUM_REVIEWS):
            review_id = str(uuid.uuid4())
            bu = random.choice(business_units)
            product = random.choice(products_services[bu])
            sentiment = random.choices(
                sentiments, weights=sentiment_weights, k=1)[0]

            review_text = generate_review_text(bu, product, sentiment)
            rating = map_sentiment_to_rating(sentiment)
            loc = random.choice(locations)
            location_str = f"{loc['city']}, {loc['state']}, {loc['country']}"

            days_offset = random.randint(0, 365)
            dt = start_date + \
                timedelta(days=days_offset, hours=random.randint(
                    0, 23), minutes=random.randint(0, 59))
            timestamp = dt.isoformat()
            date_str = dt.strftime("%Y-%m-%d")

            transaction_amount = round(random.uniform(10.0, 5000.0), 2)
            tags = f"{bu.lower()};{sentiment.lower()}"

            row = [
                review_id,
                review_text,
                random.choice(reviewer_types),
                random.choice(reviewer_names),
                bu,
                product,
                rating,
                location_str,
                loc["city"],
                loc["state"],
                loc["country"],
                timestamp,
                date_str,
                random.choice(platforms),
                random.choice(device_types),
                sentiment,  # Ground truth sentiment label
                random.choice(purchase_types),
                random.choice(customer_tiers),
                random.randint(1, 48),  # response time in hours
                random.choice([True, False]),
                random.choice(languages),
                transaction_amount,
                tags
            ]
            writer.writerow(row)
    print(f"Generated {NUM_REVIEWS} records in {filename}")


if __name__ == "__main__":
    generate_dataset(
        "e:/College/SEM 4/EDI/sentiwise-dashboard/data/reviews_dataset.csv")
