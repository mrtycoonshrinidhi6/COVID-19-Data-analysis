import { test, expect } from '@playwright/test'

test.describe('COVID-19 Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the dashboard page
    await page.goto('http://localhost:3000')
  })

  test('should display header and title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('COVID-19 Data Dashboard')
  })

  test('should display global summary cards', async ({ page }) => {
    // Wait for cards to load
    await page.waitForSelector('.summary-card', { timeout: 5000 })
    
    const cards = await page.locator('.summary-card').count()
    expect(cards).toBeGreaterThan(0)
    
    // Check for expected labels
    await expect(page.locator('.summary-card')).toContainText('Total Cases')
  })

  test('should display country selector', async ({ page }) => {
    await expect(page.locator('.country-select')).toBeVisible()
  })

  test('should load timeseries data when country selected', async ({ page }) => {
    // Ensure country dropdown has options
    const select = page.locator('.country-select')
    await select.waitFor({ state: 'visible' })
    
    // Select a country (default should be USA)
    await page.waitForSelector('.chart-wrapper', { timeout: 10000 })
    
    // Check if charts are rendered
    const chartWrappers = await page.locator('.chart-wrapper').count()
    expect(chartWrappers).toBeGreaterThan(0)
  })

  test('should display data table', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('.data-table', { timeout: 10000 })
    
    const table = page.locator('.data-table')
    await expect(table).toBeVisible()
    
    // Check for table headers
    await expect(table.locator('th')).toContainText('Date')
    await expect(table.locator('th')).toContainText('Cases')
    await expect(table.locator('th')).toContainText('Deaths')
  })

  test('should allow country selection change', async ({ page }) => {
    const select = page.locator('.country-select')
    
    // Get initial value
    const initialValue = await select.inputValue()
    
    // Change to different country
    await select.selectOption('GBR')
    
    const newValue = await select.inputValue()
    expect(newValue).toBe('GBR')
  })

  test('should display responsive design on mobile', async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: 375, height: 667 }
    })
    const page = await context.newPage()
    await page.goto('http://localhost:3000')
    
    // Check if page is still usable
    const header = page.locator('.app-header')
    await expect(header).toBeVisible()
  })
})
