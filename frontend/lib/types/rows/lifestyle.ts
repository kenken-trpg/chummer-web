// Lifestyles: row shapes listed in `Derived` (../derived.ts).

export interface InstalledLifestyleQuality {
  id: string;
  quality_id: string;
  name: string;
  category?: string;
  lp: number;
  cost: number;
  free?: boolean;
  from_freegrid?: boolean;
  multiplier?: number;
  extra?: string;
  needs_extra?: boolean;
  source?: string;
  page?: string;
}

export interface InstalledLifestyle {
  id: string;
  lifestyle_id: string;
  name: string;
  months: number;
  increment: string;
  monthly: number;
  base_monthly?: number;
  quality_monthly?: number;
  multiplier_pct?: number;
  nuyen: number;
  lp_used?: number;
  lp_max?: number;
  /** Points bought above the lifestyle's own, and how far each may go. */
  raised?: Record<"comforts" | "area" | "security", number>;
  raise_max?: Record<"comforts" | "area" | "security", number>;
  dice?: number;
  qualities?: InstalledLifestyleQuality[];
  source?: string;
}
