package com.example.noticeboard.controller;

import com.example.noticeboard.dto.PostRequest;
import com.example.noticeboard.model.Post;
import com.example.noticeboard.repository.PostRepository;
import com.example.noticeboard.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/posts")
public class PostController {
    private final PostRepository postRepository;
    private final AuthService authService;

    public PostController(PostRepository postRepository, AuthService authService) {
        this.postRepository = postRepository;
        this.authService = authService;
    }

    @GetMapping
    public List<Post> list() {
        return postRepository.findAll();
    }

    @PostMapping
    public ResponseEntity<?> create(@Valid @RequestBody PostRequest request, HttpServletRequest httpRequest) {
        // 쿠키를 FastAPI로 전달하여 사용자 검증
        String cookie = httpRequest.getHeader("Cookie");
        String username = authService.verifySession(cookie);
        
        if (username == null) {
            return ResponseEntity.status(401).body(
                new ErrorResponse("로그인이 필요합니다. http://localhost:8000/login 에서 로그인하세요.")
            );
        }
        
        Post post = new Post();
        post.setTitle(request.getTitle());
        post.setContent(request.getContent());
        post.setAuthor(username); // FastAPI에서 받은 사용자명 사용
        return ResponseEntity.ok(postRepository.save(post));
    }
    
    // 에러 응답용 내부 클래스
    private record ErrorResponse(String message) {}

    @GetMapping("/{id}")
    public ResponseEntity<Post> detail(@PathVariable Long id) {
        return postRepository.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        if (!postRepository.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        postRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
