package com.example.noticeboard.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@Service
public class AuthService {
    
    private static final String FASTAPI_URL = "http://localhost:8000/api/verify-session";
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    public AuthService() {
        this.httpClient = HttpClient.newHttpClient();
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * FastAPI 서버에 쿠키를 전달하여 사용자 검증
     * @param cookie 클라이언트에서 받은 Cookie 헤더 값
     * @return 인증된 사용자명, 실패 시 null
     */
    public String verifySession(String cookie) {
        if (cookie == null || cookie.isEmpty()) {
            return null;
        }
        
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(FASTAPI_URL))
                    .header("Cookie", cookie)
                    .GET()
                    .build();
            
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            
            if (response.statusCode() == 200) {
                JsonNode json = objectMapper.readTree(response.body());
                boolean valid = json.get("valid").asBoolean();
                
                if (valid) {
                    return json.get("username").asText();
                }
            }
            
            return null;
        } catch (Exception e) {
            System.err.println("FastAPI 세션 검증 실패: " + e.getMessage());
            return null;
        }
    }
}
