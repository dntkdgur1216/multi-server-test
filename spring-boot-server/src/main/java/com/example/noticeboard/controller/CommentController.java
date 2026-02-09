package com.example.noticeboard.controller;

import com.example.noticeboard.dto.CommentRequest;
import com.example.noticeboard.model.Comment;
import com.example.noticeboard.repository.CommentRepository;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/posts/{postId}/comments")
public class CommentController {
    private final CommentRepository commentRepository;

    public CommentController(CommentRepository commentRepository) {
        this.commentRepository = commentRepository;
    }

    @GetMapping
    public List<Comment> list(@PathVariable Long postId) {
        return commentRepository.findByPostId(postId);
    }

    @PostMapping
    public Comment create(@PathVariable Long postId, @Valid @RequestBody CommentRequest request) {
        Comment comment = new Comment();
        comment.setPostId(postId);
        comment.setContent(request.getContent());
        comment.setAuthor(request.getAuthor());
        return commentRepository.save(comment);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        if (!commentRepository.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        commentRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
