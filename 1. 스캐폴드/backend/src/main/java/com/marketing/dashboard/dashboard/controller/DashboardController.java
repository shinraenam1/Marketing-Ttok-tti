package com.marketing.dashboard.dashboard.controller;

import com.marketing.dashboard.dashboard.dto.DashboardSummaryResponse;
import com.marketing.dashboard.dashboard.service.DashboardService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "ok"));
    }

    @GetMapping("/dashboard/summary")
    public ResponseEntity<DashboardSummaryResponse> summary() {
        return ResponseEntity.ok(dashboardService.getSummary());
    }

    @PostMapping("/logic-app/analyze")
    public ResponseEntity<Map<String, Object>> analyzeWithLogicApp(
            @RequestBody Map<String, Object> analysisData) {
        return ResponseEntity.ok(dashboardService.callLogicAppAnalysis(analysisData));
    }

    @PostMapping("/logic-app/trigger")
    public ResponseEntity<Map<String, String>> triggerLogicApp() {
        return ResponseEntity.ok(dashboardService.triggerLogicApp());
    }
}
