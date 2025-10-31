.PHONY: help install run-all run-ankara run-bilkent run-ege run-gazi run-hacettepe run-itu run-izmir run-odtu clean

# Default target
help:
	@echo "Available targets:"
	@echo "  help          Show this help message"
	@echo "  install       Install dependencies using uv"
	@echo "  run-all       Run all spiders sequentially"
	@echo "  run-ankara    Run Ankara Teknokent spider"
	@echo "  run-bilkent   Run Bilkent spider"
	@echo "  run-ege       Run Ege Teknopark spider"
	@echo "  run-gazi      Run Gazi spider"
	@echo "  run-hacettepe Run Hacettepe spider"
	@echo "  run-itu       Run ITU spider"
	@echo "  run-izmir     Run Izmir Teknopark spider"
	@echo "  run-odtu      Run ODTU spider"
	@echo "  clean         Clean output directories"

# Install dependencies
install:
	uv sync

# Individual spider targets
run-ankara:
	cd teknokent_scraper && scrapy crawl ankara_teknokent_comprehensive

run-bilkent:
	cd teknokent_scraper && scrapy crawl bilkent

run-ege:
	cd teknokent_scraper && scrapy crawl ege_teknopark

run-gazi:
	cd teknokent_scraper && scrapy crawl gazi

run-hacettepe:
	cd teknokent_scraper && scrapy crawl hacettepe

run-itu:
	cd teknokent_scraper && scrapy crawl itu

run-izmir:
	cd teknokent_scraper && scrapy crawl izmir_teknopark

run-odtu:
	cd teknokent_scraper && scrapy crawl odtu

# Run all spiders sequentially
run-all: run-ankara run-bilkent run-ege run-gazi run-hacettepe run-itu run-izmir run-odtu
	@echo "All spiders have been executed"

# Clean output directories
clean:
	find teknokent_scraper/teknokent_scraper/outputs -name "*.csv" -delete
	find teknokent_scraper/teknokent_scraper/outputs -name "*.json" -delete
	@echo "Output files cleaned"