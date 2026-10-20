# Pump.fun Monitor Dashboard Skills

Skills yang diinstall untuk rebuild pump.fun monitor dashboard dengan UI modern dan fitur screening advanced.

## Installation Date
May 9, 2026 18:48 PM

## UI/UX Skills (Category: creative)

### 1. ui-ux-pro-max
- **Source**: sickn33/antigravity-awesome-skills@ui-ux-pro-max
- **Installs**: 2.2K
- **Location**: ~/.hermes/skills/creative/ui-ux-pro-max/
- **Purpose**: Professional UI/UX design patterns, modern layouts, responsive design

### 2. ui-design-system
- **Source**: samhvw8/dot-claude@ui-design-system (radix-ui-design-system)
- **Installs**: 2.8K
- **Location**: ~/.hermes/skills/creative/ui-design-system/
- **Purpose**: Design system components, tokens, consistent styling

## Crypto/Trading Skills (Category: trading)

### 3. meme-scout
- **Source**: kukapay/crypto-skills@meme-scout
- **Installs**: 117
- **Location**: ~/.hermes/skills/trading/meme-scout/
- **Purpose**: Meme coin scouting, trend detection, viral token analysis

### 4. pumpfun
- **Source**: alsk1992/cloddsbot@pumpfun
- **Installs**: 17
- **Location**: ~/.hermes/skills/trading/pumpfun/
- **Purpose**: Complete pump.fun API integration, token data, trading functions

### 5. whale-tracking
- **Source**: agiprolabs/claude-trading-skills@whale-tracking
- **Installs**: 53
- **Location**: ~/.hermes/skills/trading/whale-tracking/
- **Purpose**: Whale wallet monitoring, large transaction detection, smart money tracking

### 6. liquidity-analysis
- **Source**: agiprolabs/claude-trading-skills@liquidity-analysis
- **Installs**: 37
- **Location**: ~/.hermes/skills/trading/liquidity-analysis/
- **Purpose**: Pool liquidity analysis, depth charts, slippage calculation

### 7. custom-indicators
- **Source**: agiprolabs/claude-trading-skills@custom-indicators
- **Installs**: N/A (crypto-native indicators)
- **Location**: ~/.hermes/skills/trading/custom-indicators/
- **Purpose**: Crypto-specific technical indicators, momentum, volatility metrics

## Dashboard Context

**Current Dashboard**: ~/pump-monitor/
- Basic HTML/CSS/JS with WebSocket
- Real-time token monitoring
- Simple UI

**Rebuild Goals**:
1. Modern, professional UI/UX design
2. Advanced screening filters (whale activity, liquidity depth, momentum)
3. Real-time data visualization
4. Pump.fun API integration
5. Smart money tracking
6. Custom crypto indicators

## Usage

Skills are automatically loaded by Hermes Agent. To use:

```bash
# For UI/UX guidance
skill_view(name='ui-ux-pro-max')
skill_view(name='ui-design-system')

# For crypto functionality
skill_view(name='meme-scout')
skill_view(name='pumpfun')
skill_view(name='whale-tracking')
skill_view(name='liquidity-analysis')
skill_view(name='custom-indicators')
```

## Notes

- All skills installed via manual copy method (GitHub API rate limit)
- Source repos cloned to /tmp/
- Skills organized by category (creative vs trading)
- Ready for dashboard rebuild implementation
