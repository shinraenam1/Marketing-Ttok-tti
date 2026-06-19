package com.marketing.dashboard.integration.service;

import com.marketing.dashboard.config.AzureProperties;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;
import java.util.List;
import java.util.Map;

@Service
public class AzureOpenAiTestService {

    private static final String DEFAULT_API_VERSION = "2024-10-21";
    private static final String FOUNDRY_HOST_TOKEN = ".services.ai.azure.com";

    private final RestClient restClient;
    private final AzureProperties azureProperties;

    public AzureOpenAiTestService(RestClient.Builder restClientBuilder, AzureProperties azureProperties) {
        this.restClient = restClientBuilder.build();
        this.azureProperties = azureProperties;
    }

    public Map<String, Object> chatTest(String prompt) {
        String endpoint = trimTrailingSlash(azureProperties.endpoint());
        boolean isFoundryEndpoint = isFoundryEndpoint(endpoint);

        Map<String, Object> payload = Map.of(
                "model", azureProperties.deployment() == null ? "" : azureProperties.deployment().trim(),
                "messages", List.of(
                        Map.of("role", "system", "content", "You are a helpful assistant for marketing analytics."),
                        Map.of("role", "user", "content", prompt)
                ),
                "max_completion_tokens", 256,
                "reasoning_effort", "medium"
        );

        URI uri = buildUri(endpoint, isFoundryEndpoint);
        RestClient.RequestBodySpec request = restClient.post()
                .uri(uri)
                .contentType(MediaType.APPLICATION_JSON);

        if (isFoundryEndpoint) {
            request = request.header("Authorization", "Bearer " + azureProperties.apiKey());
        } else {
            request = request.header("api-key", azureProperties.apiKey());
        }

        Map<String, Object> response = request
                .body(payload)
                .retrieve()
                .body(Map.class);

        return Map.of(
                "called", true,
                "endpoint", uri.toString(),
                "authType", isFoundryEndpoint ? "Bearer" : "api-key",
                "response", response == null ? Map.of() : response
        );
    }

    private URI buildUri(String endpoint, boolean isFoundryEndpoint) {
        String path;
        if (isFoundryEndpoint) {
            path = resolveFoundryBaseEndpoint(endpoint) + "/openai/v1/chat/completions";
        } else if (endpoint.contains("/openai/deployments/")) {
            path = endpoint + "/chat/completions";
        } else {
            String deployment = azureProperties.deployment() == null ? "" : azureProperties.deployment().trim();
            path = endpoint + "/openai/deployments/" + deployment + "/chat/completions";
        }

        if (isFoundryEndpoint) {
            return URI.create(path);
        }

        return UriComponentsBuilder
                .fromUriString(path)
            .queryParam("api-version", DEFAULT_API_VERSION)
                .build(true)
                .toUri();
    }

    private String trimTrailingSlash(String text) {
        if (text == null || text.isBlank()) {
            return "";
        }
        return text.endsWith("/") ? text.substring(0, text.length() - 1) : text;
    }

    private boolean isFoundryEndpoint(String endpoint) {
        return endpoint.contains(FOUNDRY_HOST_TOKEN);
    }

    private String resolveFoundryBaseEndpoint(String endpoint) {
        int projectPathIndex = endpoint.indexOf("/api/projects/");
        if (projectPathIndex > 0) {
            return endpoint.substring(0, projectPathIndex);
        }
        return endpoint;
    }
}
