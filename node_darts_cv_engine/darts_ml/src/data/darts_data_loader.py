"""
Data loader for professional darts match results.

Supports multiple data sources:
- Kaggle datasets (PDC, BDO)
- Web scraping (pdc.tv, dartsdatabase.co.uk)
- CSV files
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
from loguru import logger

from ..utils.config import get_config


class DartsDataLoader:
    """Load and validate darts match data from multiple sources."""
    
    def __init__(self):
        """Initialize data loader with configuration."""
        self.config = get_config()
        self.raw_data_path = self.config.data_raw_path
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        
    def load_from_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load darts match data from CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with match data
        """
        logger.info(f"Loading data from CSV: {file_path}")
        
        df = pd.read_csv(file_path)
        df = self._validate_and_clean(df)
        
        logger.info(f"Loaded {len(df)} matches from CSV")
        return df
    
    def scrape_pdc_results(
        self,
        start_year: int = 2020,
        end_year: Optional[int] = None,
        max_pages: int = 100
    ) -> pd.DataFrame:
        """
        Scrape match results from PDC website.
        
        Args:
            start_year: Starting year for data collection
            end_year: Ending year (defaults to current year)
            max_pages: Maximum number of pages to scrape
            
        Returns:
            DataFrame with PDC match results
        """
        if end_year is None:
            end_year = datetime.now().year
        
        logger.info(f"Scraping PDC results from {start_year} to {end_year}")
        
        all_matches = []
        base_url = "https://www.pdc.tv/results"
        
        for year in range(start_year, end_year + 1):
            logger.info(f"Scraping year: {year}")
            
            for page in range(1, max_pages + 1):
                try:
                    # Add delay to be respectful to server
                    time.sleep(1)
                    
                    url = f"{base_url}?year={year}&page={page}"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Parse match results from page
                    matches = self._parse_pdc_page(soup, year)
                    
                    if not matches:
                        logger.info(f"No more matches found for {year} at page {page}")
                        break
                    
                    all_matches.extend(matches)
                    logger.debug(f"Scraped {len(matches)} matches from page {page}")
                    
                except requests.RequestException as e:
                    logger.warning(f"Error scraping page {page} for year {year}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error scraping year {year}, page {page}: {e}")
                    continue
        
        if not all_matches:
            logger.warning("No matches scraped from PDC")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_matches)
        df = self._validate_and_clean(df)
        
        # Save to raw data directory
        output_path = self.raw_data_path / f"pdc_results_{start_year}_{end_year}.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} PDC matches to {output_path}")
        
        return df
    
    def _parse_pdc_page(self, soup: BeautifulSoup, year: int) -> List[Dict[str, Any]]:
        """
        Parse PDC results page HTML.
        
        Args:
            soup: BeautifulSoup object of page
            year: Year of matches
            
        Returns:
            List of match dictionaries
        """
        matches = []
        
        # NOTE: This is a template - actual selectors need to be updated
        # based on the real PDC website structure
        match_elements = soup.find_all('div', class_='match-result')
        
        for match_elem in match_elements:
            try:
                match_data = {
                    'date': self._extract_date(match_elem, year),
                    'tournament': self._extract_text(match_elem, 'tournament-name'),
                    'player1': self._extract_text(match_elem, 'player1-name'),
                    'player2': self._extract_text(match_elem, 'player2-name'),
                    'score1': self._extract_score(match_elem, 'player1-score'),
                    'score2': self._extract_score(match_elem, 'player2-score'),
                    'winner': self._extract_text(match_elem, 'winner-name'),
                    'source': 'pdc_scrape'
                }
                
                # Only add if we have minimum required fields
                if match_data['player1'] and match_data['player2']:
                    matches.append(match_data)
                    
            except Exception as e:
                logger.debug(f"Error parsing match element: {e}")
                continue
        
        return matches
    
    def scrape_dartsdatabase(
        self,
        start_year: int = 2020,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Scrape match results from dartsdatabase.co.uk.
        
        Args:
            start_year: Starting year for data collection
            end_year: Ending year (defaults to current year)
            
        Returns:
            DataFrame with match results
        """
        if end_year is None:
            end_year = datetime.now().year
        
        logger.info(f"Scraping dartsdatabase from {start_year} to {end_year}")
        
        all_matches = []
        base_url = "https://www.dartsdatabase.co.uk"
        
        # NOTE: This is a template implementation
        # Actual implementation depends on website structure
        
        logger.warning("dartsdatabase scraper is a template - needs implementation")
        
        return pd.DataFrame()
    
    def download_kaggle_dataset(self, dataset_name: str) -> pd.DataFrame:
        """
        Download darts dataset from Kaggle.
        
        Args:
            dataset_name: Kaggle dataset identifier (e.g., 'user/dataset-name')
            
        Returns:
            DataFrame with match data
        """
        logger.info(f"Downloading Kaggle dataset: {dataset_name}")
        
        try:
            # Requires kaggle API credentials in ~/.kaggle/kaggle.json
            import kaggle
            
            # Download to raw data directory
            kaggle.api.dataset_download_files(
                dataset_name,
                path=str(self.raw_data_path),
                unzip=True
            )
            
            # Find CSV files in downloaded data
            csv_files = list(self.raw_data_path.glob("*.csv"))
            
            if not csv_files:
                logger.warning(f"No CSV files found in downloaded dataset: {dataset_name}")
                return pd.DataFrame()
            
            # Load and combine all CSV files
            dfs = []
            for csv_file in csv_files:
                df = pd.read_csv(csv_file)
                dfs.append(df)
            
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df = self._validate_and_clean(combined_df)
            
            logger.info(f"Loaded {len(combined_df)} matches from Kaggle dataset")
            return combined_df
            
        except ImportError:
            logger.error("Kaggle package not installed. Run: pip install kaggle")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error downloading Kaggle dataset: {e}")
            return pd.DataFrame()
    
    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean match data.
        
        Args:
            df: Raw match data
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        logger.info(f"Validating {len(df)} matches")
        
        # Standardize column names
        df = self._standardize_columns(df)
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['date', 'player1', 'player2'], keep='first')
        if len(df) < initial_count:
            logger.info(f"Removed {initial_count - len(df)} duplicate matches")
        
        # Convert date to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
        
        # Remove matches with missing players
        df = df.dropna(subset=['player1', 'player2'])
        
        # Sort by date (critical for temporal ordering)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Add match_id
        df['match_id'] = range(len(df))
        
        logger.info(f"Validation complete: {len(df)} valid matches")
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names across different data sources.
        
        Args:
            df: DataFrame with varying column names
            
        Returns:
            DataFrame with standardized columns
        """
        # Common column name mappings
        column_mapping = {
            'Date': 'date',
            'DATE': 'date',
            'match_date': 'date',
            'Player 1': 'player1',
            'Player1': 'player1',
            'player_1': 'player1',
            'Player 2': 'player2',
            'Player2': 'player2',
            'player_2': 'player2',
            'Winner': 'winner',
            'WINNER': 'winner',
            'Tournament': 'tournament',
            'TOURNAMENT': 'tournament',
            'Event': 'tournament',
            'Score1': 'score1',
            'Score2': 'score2',
        }
        
        df = df.rename(columns=column_mapping)
        
        return df
    
    def _extract_text(self, element: BeautifulSoup, class_name: str) -> Optional[str]:
        """Extract text from HTML element by class name."""
        found = element.find(class_=class_name)
        return found.get_text(strip=True) if found else None
    
    def _extract_score(self, element: BeautifulSoup, class_name: str) -> Optional[int]:
        """Extract score from HTML element."""
        text = self._extract_text(element, class_name)
        if text:
            try:
                return int(text)
            except ValueError:
                return None
        return None
    
    def _extract_date(self, element: BeautifulSoup, year: int) -> Optional[str]:
        """Extract and format date from HTML element."""
        date_text = self._extract_text(element, 'match-date')
        if date_text:
            try:
                # Try to parse date (format depends on website)
                # This is a template - adjust based on actual format
                return f"{year}-{date_text}"
            except Exception:
                return None
        return None
    
    def load_all_sources(self) -> pd.DataFrame:
        """
        Load data from all available sources and combine.
        
        Returns:
            Combined DataFrame with all match data
        """
        logger.info("Loading data from all sources")
        
        all_dfs = []
        
        # Load existing CSV files from raw data directory
        csv_files = list(self.raw_data_path.glob("*.csv"))
        for csv_file in csv_files:
            try:
                df = self.load_from_csv(str(csv_file))
                all_dfs.append(df)
            except Exception as e:
                logger.warning(f"Error loading {csv_file}: {e}")
        
        if not all_dfs:
            logger.warning("No data loaded from any source")
            return pd.DataFrame()
        
        # Combine all data
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df = self._validate_and_clean(combined_df)
        
        logger.info(f"Total matches loaded: {len(combined_df)}")
        logger.info(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
        
        return combined_df
