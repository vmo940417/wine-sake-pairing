export type BeverageType = 'wine' | 'sake' | 'whisky' | 'brandy' | 'chinese' | 'korean';

export type PriceLink = { label: string; url: string };

export type Reason = { text: string; impact: number };

export type BeverageProfile = {
  acidity: number;
  tannin: number;
  body: number;
  sweetness: number;
  alcohol: number;
  umami: number;
  aroma: number;
  oak: number;
};

export type BeverageDetail = {
  id: string;
  type: BeverageType;
  category: string;
  abv: number;
  name_ko: string;
  name_en: string;
  aliases: string[];
  profile: BeverageProfile;
  summary: string;
  regions: string[];
  serving_temp: string;
  pairs_with: string[];
  bottles: string[];
  price_links: PriceLink[];
};

export type Food = {
  id: string;
  name_ko: string;
  aliases: string[];
  cuisine: string;
  protein: string;
  tags: string[];
};

export type PairingResult = {
  beverage_id: string;
  type: BeverageType;
  category: string;
  name_ko: string;
  name_en: string;
  score: number;
  reasons: Reason[];
  price_links: PriceLink[];
};

export type PairingResponse = {
  food: Food;
  food_source: 'db' | 'ai' | 'keyword';
  results: PairingResult[];
};

export type ProductSummary = {
  name: string;
  type: BeverageType;
  producer: string;
  region: string;
  style: string;
  description: string;
  food_pairings: string[];
  related_beverage_id: string | null;
};

export type DictionaryResponse = {
  query: string;
  beverage: BeverageDetail | null;
  product: ProductSummary | null;
  product_source: 'ai' | null;
  price_link: PriceLink;
};
