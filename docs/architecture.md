# Architecture

## Purpose

A Telegram economy bot that rewards chat activity, supports referrals, tracks balances and exposes admin controls.

## Main flow

`	ext
Telegram update -> bot.py handlers -> reward/referral rules -> storage.py SQLite layer -> bot/admin UI response
`

## Design notes

Feature flags and admin screens make it possible to stage rollout without exposing every mechanic at once.

## Portfolio note

This repository is packaged for review. Some runtime integrations require local credentials or external services and are represented with .env.example instead of real secrets.
