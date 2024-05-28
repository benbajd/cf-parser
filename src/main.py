from paths import Path
import scraper

path_cf = Path(['Users', 'benbajd', 'Documents', 'cp', 'codeforces'])

print(scraper.cf_problems_scrape(1977))
