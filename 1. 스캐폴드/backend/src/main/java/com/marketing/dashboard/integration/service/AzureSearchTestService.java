package com.marketing.dashboard.integration.service;

import com.marketing.dashboard.config.AzureSearchProperties;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;
import java.util.Map;

@Service
public class AzureSearchTestService {

    private static final String DEFAULT_API_VERSION = "2024-07-01";

    private final RestClient restClient;
    private final AzureSearchProperties azureSearchProperties;

    public AzureSearchTestService(RestClient.Builder restClientBuilder, AzureSearchProperties azureSearchProperties) {
        this.restClient = restClientBuilder.build();
        this.azureSearchProperties = azureSearchProperties;
    }

    public Map<String, Object> listIndexes() {
        URI uri = UriComponentsBuilder
                .fromUriString(trimTrailingSlash(azureSearchProperties.endpoint()) + "/indexes")
                .queryParam("api-version", DEFAULT_API_VERSION)
                .build(true)
                .toUri();

        Map<String, Object> response = restClient.get()
                .uri(uri)
                .header("api-key", azureSearchProperties.apiKey())
                .retrieve()
                .body(Map.class);

        return Map.of(
                "called", true,
                "endpoint", uri.toString(),
                "response", response == null ? Map.of() : response
        );
    }

    public Map<String, Object> searchDocuments(String indexName, String query, int top) {
        URI uri = UriComponentsBuilder
                .fromUriString(trimTrailingSlash(azureSearchProperties.endpoint()))
                .pathSegment("indexes", indexName, "docs", "search")
                .queryParam("api-version", DEFAULT_API_VERSION)
                .build(true)
                .toUri();

        Map<String, Object> payload = Map.of(
                "search", query,
                "top", top,
                "count", true
        );

        Map<String, Object> response = restClient.post()
                .uri(uri)
                .contentType(MediaType.APPLICATION_JSON)
                .header("api-key", azureSearchProperties.apiKey())
                .body(payload)
                .retrieve()
                .body(Map.class);

        return Map.of(
                "called", true,
                "endpoint", uri.toString(),
                "response", response == null ? Map.of() : response
        );
    }

    private String trimTrailingSlash(String text) {
        if (text == null || text.isBlank()) {
            return "";
        }
        return text.endsWith("/") ? text.substring(0, text.length() - 1) : text;
    }
}
