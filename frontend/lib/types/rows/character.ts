// Martial arts, contacts and exotic skills: row shapes listed in `Derived` (../derived.ts).

export interface InstalledMartialArtTechnique {
  id: string;
  name: string;
  free: boolean;
  karma: number;
  source?: string;
  page?: string;
}

export interface InstalledMartialArt {
  id: string;
  art_id: string;
  name: string;
  source?: string;
  page?: string;
  style_karma: number;
  karma: number;
  free?: boolean;
  locked?: boolean;
  source_quality_id?: string | null;
  techniques: InstalledMartialArtTechnique[];
  technique_options: string[];
  technique_max?: number | null;
}

export interface InstalledContact {
  id: string;
  name: string;
  role?: string;
  connection: number;
  loyalty: number;
  cost: number;
  billable?: number;
  connection_max: number;
  loyalty_max: number;
  loyalty_min?: number;
  group?: boolean;
  free?: boolean;
  forced_loyalty?: number | null;
  source_quality_id?: string | null;
  locked?: boolean;
  black_market_pipeline?: boolean;
}

export interface InstalledExoticSkill {
  id: string;
  skill_name: string;
  extra: string;
  label: string;
  rating: number;
  rating_max: number;
  attribute: string;
  category: string;
  options: string[];
  source?: string;
}
