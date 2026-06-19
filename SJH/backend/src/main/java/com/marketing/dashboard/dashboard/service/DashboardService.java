package com.marketing.dashboard.dashboard.service;

import com.marketing.dashboard.dashboard.dto.DashboardSummaryResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class DashboardService {

    private final RestTemplate restTemplate;

    @Value("${azure.logic-app.workflow-id:marketing-ttok-tti-functionappv2-30m}")
    private String workflowId;

    @Value("${azure.logic-app.subscription-id:80aed1b5-83fd-4160-911b-039f86fd7aa5}")
    private String subscriptionId;

    @Value("${azure.logic-app.resource-group:Marketing-Ttok-tti}")
    private String resourceGroup;

    public DashboardService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public DashboardSummaryResponse getSummary() {
        return new DashboardSummaryResponse(
                12,
                1830.75,
                0.047,
                List.of("Search", "Social", "Email")
        );
    }

    public Map<String, Object> callLogicAppAnalysis(Map<String, Object> analysisData) {
        try {
            // 실제 Logic App analyze_result 엔드포인트 호출
            // 또는 Azure Functions API 호출
            Map<String, Object> result = new HashMap<>();
            result.put("status", "success");
            result.put("data", analysisData);
            result.put("timestamp", System.currentTimeMillis());
            return result;
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("status", "error");
            errorResult.put("message", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, String> triggerLogicApp() {
        try {
            String url = String.format(
                    "https://management.azure.com/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Logic/workflows/%s/triggers/Recurrence/run?api-version=2019-05-01",
                    subscriptionId, resourceGroup, workflowId
            );

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            // Authorization header는 별도로 설정 필요 (Azure AD token)

            HttpEntity<String> entity = new HttpEntity<>("{}", headers);

            restTemplate.postForObject(url, entity, String.class);

            Map<String, String> response = new HashMap<>();
            response.put("status", "triggered");
            response.put("message", "Logic App trigger sent successfully");
            return response;
        } catch (Exception e) {
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("status", "error");
            errorResponse.put("message", e.getMessage());
            return errorResponse;
        }
    }
}
