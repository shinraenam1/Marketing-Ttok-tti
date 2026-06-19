package com.marketing.dashboard.dashboard.dto;

import java.util.List;

public record DashboardSummaryResponse(
        int totalCampaigns,
        double spendToday,
        double conversionRate,
        List<String> topChannels
) {
}
