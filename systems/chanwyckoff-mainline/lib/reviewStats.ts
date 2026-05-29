export type ReviewFailureStats = {
  manual_failure_reasons: Record<string, number>;
  llm_failure_types: Record<string, number>;
  total_failed_records: number;
};

export const fallbackReviewFailureStats: ReviewFailureStats = {
  manual_failure_reasons: {
    supply_returned: 2,
    time_stop: 1,
  },
  llm_failure_types: {
    heavy_volume_close_back_inside: 1,
  },
  total_failed_records: 3,
};

export async function fetchReviewFailureStats(): Promise<ReviewFailureStats> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${baseUrl}/api/reviews/stats/failures`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Review failure stats request failed: ${response.status}`);
  }
  return response.json() as Promise<ReviewFailureStats>;
}
