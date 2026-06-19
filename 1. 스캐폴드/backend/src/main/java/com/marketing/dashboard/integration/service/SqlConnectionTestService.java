package com.marketing.dashboard.integration.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class SqlConnectionTestService {

    private final JdbcTemplate jdbcTemplate;

    public SqlConnectionTestService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public Map<String, Object> ping() {
        Integer dbPing = jdbcTemplate.queryForObject("SELECT 1", Integer.class);
        return Map.of(
                "connected", true,
                "dbPing", dbPing == null ? -1 : dbPing
        );
    }
}
