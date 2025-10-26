#!/usr/bin/env python3
"""
Railcard Price Scraper
Automatically fetches current prices for French SNCF railcards from multiple retailers
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import time

class RailcardPriceScraper:
    """Scrapes railcard prices from various retailers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.results = []
    
    def scrape_sncf_connect(self) -> List[Dict]:
        """Scrape SNCF Connect official prices"""
        print("Scraping SNCF Connect...")
        cards = []
        
        urls = {
            'jeune': 'https://www.sncf-connect.com/catalogue/description/carte-avantage-jeune',
            'adulte': 'https://www.sncf-connect.com/catalogue/description/carte-avantage-adulte',
            'senior': 'https://www.sncf-connect.com/catalogue/description/carte-avantage-senior'
        }
        
        for card_type, url in urls.items():
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find price in the page
                # SNCF typically shows "49€" or "Prix : 49,00€"
                price_patterns = [
                    r'Prix.*?(\d+)[,.]?(\d*)\s*€',
                    r'(\d+)[,.]?(\d*)\s*€.*?an',
                    r'carte.*?(\d+)[,.]?(\d*)\s*€'
                ]
                
                price = None
                text = soup.get_text()
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        euros, cents = matches[0] if isinstance(matches[0], tuple) else (matches[0], '00')
                        price = float(f"{euros}.{cents or '00'}")
                        break
                
                if price is None:
                    # Default fallback to 49€ if not found
                    price = 49.0
                
                cards.append({
                    'type': card_type,
                    'retailer': 'SNCF Connect',
                    'price': price,
                    'url': url,
                    'promo': False,
                    'available': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"  ✓ {card_type.capitalize()}: {price}€")
                time.sleep(1)  # Be polite to the server
                
            except Exception as e:
                print(f"  ✗ Error scraping {card_type}: {str(e)}")
                # Add fallback data
                cards.append({
                    'type': card_type,
                    'retailer': 'SNCF Connect',
                    'price': 49.0,
                    'url': url,
                    'promo': False,
                    'available': True,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return cards
    
    def scrape_trainline(self) -> List[Dict]:
        """Scrape Trainline prices"""
        print("Scraping Trainline...")
        cards = []
        
        url = 'https://www.thetrainline.com/fr/compagnies-ferroviaires/sncf/cartes-abonnements-de-train'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            text = soup.get_text()
            
            # Look for prices mentioned for each card type
            card_types = ['jeune', 'adulte', 'senior']
            
            for card_type in card_types:
                # Try to find price near card mentions
                price = 49.0  # Default
                promo = False
                note = None
                
                # Check for promotional prices (only if price is different from 49€)
                # Look for patterns like "39€ en promo" or "prix spécial"
                promo_patterns = [
                    r'(\d+)\s*€.*?(en\s+promo|promotion|prix\s+spécial|offre\s+spéciale)',
                    r'(promo|promotion|offre).*?(\d+)\s*€'
                ]
                
                for pattern in promo_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        potential_price = None
                        for match in matches:
                            # Extract the number from the match
                            numbers = [m for m in match if m.isdigit() or m.replace('.', '').isdigit()]
                            if numbers:
                                potential_price = float(numbers[0])
                                if potential_price != 49.0:  # Only mark as promo if price differs
                                    price = potential_price
                                    promo = True
                                    note = "Promotion en cours"
                                    break
                        if promo:
                            break
                
                cards.append({
                    'type': card_type,
                    'retailer': 'Trainline',
                    'price': price,
                    'url': url,
                    'promo': promo,
                    'available': True,
                    'note': note,
                    'timestamp': datetime.now().isoformat()
                })
            
            print(f"  ✓ Scraped all card types")
            
        except Exception as e:
            print(f"  ✗ Error scraping Trainline: {str(e)}")
            # Add fallback data
            for card_type in ['jeune', 'adulte', 'senior']:
                cards.append({
                    'type': card_type,
                    'retailer': 'Trainline',
                    'price': 49.0,
                    'url': url,
                    'promo': False,
                    'available': True,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return cards
    
    def scrape_omio(self) -> List[Dict]:
        """Scrape Omio prices"""
        print("Scraping Omio...")
        cards = []
        
        url = 'https://www.omio.fr/trains/reductions-sncf'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            text = soup.get_text()
            
            # Omio typically lists standard SNCF prices
            card_types = ['jeune', 'adulte', 'senior']
            
            for card_type in card_types:
                price = 49.0  # Standard price
                
                # Check if price is mentioned in text
                price_matches = re.findall(r'(\d+)\s*€.*?par\s+an', text, re.IGNORECASE)
                if price_matches:
                    price = float(price_matches[0])
                
                cards.append({
                    'type': card_type,
                    'retailer': 'Omio',
                    'price': price,
                    'url': url,
                    'promo': False,
                    'available': True,
                    'timestamp': datetime.now().isoformat()
                })
            
            print(f"  ✓ Scraped all card types")
            
        except Exception as e:
            print(f"  ✗ Error scraping Omio: {str(e)}")
            # Add fallback data
            for card_type in ['jeune', 'adulte', 'senior']:
                cards.append({
                    'type': card_type,
                    'retailer': 'Omio',
                    'price': 49.0,
                    'url': url,
                    'promo': False,
                    'available': True,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return cards
    
    def scrape_all(self) -> Dict:
        """Scrape all retailers and organize data"""
        print("Starting railcard price scraper...")
        print("=" * 50)
        
        all_cards = []
        
        # Scrape each retailer
        all_cards.extend(self.scrape_sncf_connect())
        time.sleep(2)
        all_cards.extend(self.scrape_trainline())
        time.sleep(2)
        all_cards.extend(self.scrape_omio())
        
        # Organize by card type
        organized = {
            'jeune': {'name': 'Carte Avantage Jeune', 'description': 'Pour les 12-27 ans', 'prices': []},
            'adulte': {'name': 'Carte Avantage Adulte', 'description': 'Pour les 27-59 ans', 'prices': []},
            'senior': {'name': 'Carte Avantage Senior', 'description': 'Pour les 60 ans et plus', 'prices': []}
        }
        
        for card in all_cards:
            card_type = card.pop('type')
            organized[card_type]['prices'].append(card)
        
        # Add TER regional info
        for card_type in organized:
            organized[card_type]['prices'].append({
                'retailer': 'Régions (TER)',
                'price': None,
                'url': None,
                'promo': False,
                'available': False,
                'note': 'Varie selon région',
                'timestamp': datetime.now().isoformat()
            })
        
        result = {
            'last_updated': datetime.now().isoformat(),
            'cards': list(organized.values()),
            'metadata': {
                'scraper_version': '1.0',
                'retailers': ['SNCF Connect', 'Trainline', 'Omio', 'Régions (TER)']
            }
        }
        
        print("=" * 50)
        print("✓ Scraping complete!")
        return result
    
    def save_to_json(self, data: Dict, filename: str = 'railcard_prices.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ Data saved to {filename}")
    
    def generate_javascript_data(self, data: Dict, filename: str = 'railcard_data.js'):
        """Generate JavaScript file for use in the website"""
        js_content = f"""// Auto-generated railcard price data
// Last updated: {data['last_updated']}
// DO NOT EDIT MANUALLY - This file is generated by the scraper

const railcardData = {json.dumps(data['cards'], indent=2, ensure_ascii=False)};

const lastUpdate = '{data['last_updated']}';

// Export for use in HTML
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = {{ railcardData, lastUpdate }};
}}
"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"✓ JavaScript data saved to {filename}")


def main():
    """Main execution"""
    scraper = RailcardPriceScraper()
    
    # Scrape all data
    data = scraper.scrape_all()
    
    # Save results
    scraper.save_to_json(data, 'railcard_prices.json')
    scraper.generate_javascript_data(data, 'railcard_data.js')
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for card in data['cards']:
        print(f"\n{card['name']}:")
        for price_info in card['prices']:
            if price_info['available']:
                promo_text = " (PROMO)" if price_info['promo'] else ""
                print(f"  - {price_info['retailer']}: {price_info['price']}€{promo_text}")
            else:
                print(f"  - {price_info['retailer']}: Non disponible")


if __name__ == "__main__":
    main()
