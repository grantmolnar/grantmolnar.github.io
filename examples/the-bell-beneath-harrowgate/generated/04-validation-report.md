# Validation Report

Result: PASS

Computed necessary-encounter edge connectivity: 3

## Minimum-Cut Witness

**Configured minimum connectivity:** 3  
**Partition A:** `cracked-chapterhouse`  
**Partition B:** `black-rain-cistern`, `chain-scriptorium`, `choir-of-iron-tongues`, `counterweight-wells`, `deep-bell`, `feast-of-empty-chairs`, `garden-of-teeth`, `hall-of-bent-knees`, `inverted-chapel`, `kings-narrow-grave`, `lantern-cistern`, `menagerie-of-quiet-beasts`, `mouth-below`, `quarry-cleft`, `reliquary-under-water`, `ropeworks-of-three-burdens`, `salt-barracks`  
**Cut edges:** `chain-scriptorium`—`cracked-chapterhouse`, `cracked-chapterhouse`—`hall-of-bent-knees`, `cracked-chapterhouse`—`ropeworks-of-three-burdens`

## Findings

- **WARNING multiple-start-encounters**: More than one encounter is marked as the adventure's start: 'cracked-chapterhouse', 'quarry-cleft'.
  **Repair:** Keep one start encounter unless the adventure intentionally offers several openings.
- **WARNING multiple-end-encounters**: More than one encounter is marked as an adventure end: 'deep-bell', 'mouth-below'.
  **Repair:** Keep one end encounter unless the adventure intentionally has several finales.
