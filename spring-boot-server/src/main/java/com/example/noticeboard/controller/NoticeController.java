package com.example.noticeboard.controller;

import com.example.noticeboard.dto.NoticeRequest;
import com.example.noticeboard.model.Notice;
import com.example.noticeboard.repository.NoticeRepository;
import com.example.noticeboard.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/notices")
public class NoticeController {
    private final NoticeRepository noticeRepository;
    private final AuthService authService;

    public NoticeController(NoticeRepository noticeRepository, AuthService authService) {
        this.noticeRepository = noticeRepository;
        this.authService = authService;
    }

    @GetMapping
    public List<Notice> list() {
        return noticeRepository.findAll();
    }

    @PostMapping
    public ResponseEntity<?> create(@Valid @RequestBody NoticeRequest request, HttpServletRequest httpRequest) {
        // 쿠키를 FastAPI로 전달하여 사용자 검증
        String cookie = httpRequest.getHeader("Cookie");
        String username = authService.verifySession(cookie);
        
        if (username == null) {
            return ResponseEntity.status(401).body(
                new ErrorResponse("로그인이 필요합니다. http://localhost:8000/login 에서 로그인하세요.")
            );
        }
        
        Notice notice = new Notice();
        notice.setTitle(request.getTitle());
        notice.setContent(request.getContent());
        notice.setAuthor(username); // FastAPI에서 받은 사용자명 사용
        return ResponseEntity.ok(noticeRepository.save(notice));
    }
    
    // 에러 응답용 내부 클래스
    private record ErrorResponse(String message) {}

    @GetMapping("/{id}")
    public ResponseEntity<Notice> detail(@PathVariable Long id) {
        return noticeRepository.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        if (!noticeRepository.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        noticeRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
