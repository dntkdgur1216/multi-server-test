package com.example.noticeboard.dto;

import jakarta.validation.constraints.NotBlank;

public class CommentRequest {
    @NotBlank
    private String content;

    @NotBlank
    private String author;

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }
}
