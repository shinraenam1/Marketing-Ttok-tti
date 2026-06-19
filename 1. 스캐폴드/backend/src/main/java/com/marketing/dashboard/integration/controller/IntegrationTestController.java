package com.marketing.dashboard.integration.controller;

import com.marketing.dashboard.integration.service.AzureOpenAiTestService;
import com.marketing.dashboard.integration.service.AzureSearchTestService;
import com.marketing.dashboard.integration.service.SqlConnectionTestService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/integration")
public class IntegrationTestController {

    private final SqlConnectionTestService sqlConnectionTestService;
    private final AzureOpenAiTestService azureOpenAiTestService;
    private final AzureSearchTestService azureSearchTestService;

    public IntegrationTestController(
            SqlConnectionTestService sqlConnectionTestService,
            AzureOpenAiTestService azureOpenAiTestService,
            AzureSearchTestService azureSearchTestService
    ) {
        this.sqlConnectionTestService = sqlConnectionTestService;
        this.azureOpenAiTestService = azureOpenAiTestService;
        this.azureSearchTestService = azureSearchTestService;
    }

    @GetMapping("/sql/ping")
    public ResponseEntity<Map<String, Object>> sqlPing() {
        try {
            return ResponseEntity.ok(sqlConnectionTestService.ping());
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(Map.of(
                            "connected", false,
                            "error", ex.getClass().getSimpleName(),
                            "message", sanitizeMessage(ex)
                    ));
        }
    }

    @GetMapping("/openai/chat-test")
    public ResponseEntity<Map<String, Object>> openAiChatTest(
            @RequestParam(defaultValue = "Say hello from Azure OpenAI test endpoint.") String prompt
    ) {
        try {
            return ResponseEntity.ok(azureOpenAiTestService.chatTest(prompt));
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(Map.of(
                            "called", false,
                            "error", ex.getClass().getSimpleName(),
                            "message", sanitizeMessage(ex)
                    ));
        }
    }

    @GetMapping("/search/indexes")
    public ResponseEntity<Map<String, Object>> listSearchIndexes() {
        try {
            return ResponseEntity.ok(azureSearchTestService.listIndexes());
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(Map.of(
                            "called", false,
                            "error", ex.getClass().getSimpleName(),
                            "message", sanitizeMessage(ex)
                    ));
        }
    }

    @GetMapping("/search/query")
    public ResponseEntity<Map<String, Object>> querySearch(
            @RequestParam String indexName,
            @RequestParam(defaultValue = "*") String q,
            @RequestParam(defaultValue = "3") int top
    ) {
        try {
            return ResponseEntity.ok(azureSearchTestService.searchDocuments(indexName, q, top));
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(Map.of(
                            "called", false,
                            "error", ex.getClass().getSimpleName(),
                            "message", sanitizeMessage(ex)
                    ));
        }
    }

    private String sanitizeMessage(Exception ex) {
        String message = ex.getMessage();
        if (message == null || message.isBlank()) {
            return "No error message";
        }
        return message.length() > 500 ? message.substring(0, 500) : message;
    }
}
