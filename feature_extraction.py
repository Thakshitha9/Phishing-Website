import numpy as np
from urllib.parse import urlparse
import re

def extract_features(url):
    features = []

    # 1. URL length
    features.append(len(url))

    # 2. HTTPS usage
    features.append(1 if url.startswith("https") else 0)

    # 3. Presence of @
    features.append(1 if "@" in url else 0)

    # 4. Hyphen in domain
    domain = urlparse(url).netloc
    features.append(1 if "-" in domain else 0)

    # 5. Number of dots
    features.append(domain.count("."))

    # 6. IP address in URL
    ip_pattern = r'(\d{1,3}\.){3}\d{1,3}'
    features.append(1 if re.search(ip_pattern, url) else 0)

    # 7. URL contains suspicious words
    suspicious_words = ["login", "verify", "update", "bank", "secure"]
    features.append(1 if any(word in url.lower() for word in suspicious_words) else 0)

    return features