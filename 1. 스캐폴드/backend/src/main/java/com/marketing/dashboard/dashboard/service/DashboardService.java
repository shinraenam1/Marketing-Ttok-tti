package com.marketing.dashboard.dashboard.service;

import com.marketing.dashboard.dashboard.dto.DashboardSummaryResponse;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DashboardService {

    public DashboardSummaryResponse getSummary() {
        return new DashboardSummaryResponse(
                12,
                1830.75,
                0.047,
                List.of("Search", "Social", "Email")
        );
    }
}
