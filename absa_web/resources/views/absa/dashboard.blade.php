{{-- resources/views/absa/dashboard.blade.php --}}
<!doctype html>
<html lang="id">

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>LUXUEX • ABSA Dashboard</title>

  <style>
    :root {
      --bg: #050508;
      --text: #f5f5f7;
      --muted: rgba(255, 255, 255, .70);
      --muted2: rgba(255, 255, 255, .52);

      --gold: #d6b54a;
      --gold2: #a77b10;
      --goldLine: rgba(214, 181, 74, .45);

      --panelA: rgba(255, 255, 255, .045);
      --panelB: rgba(255, 255, 255, .020);
      --line: rgba(255, 255, 255, .08);

      --shadow: 0 18px 70px rgba(0, 0, 0, .70);
      --inner: inset 0 0 0 1px rgba(0, 0, 0, .25), inset 0 10px 30px rgba(0, 0, 0, .40);
      --glow: 0 0 0 1px rgba(214, 181, 74, .22), 0 25px 80px rgba(214, 181, 74, .12);

      --r: 22px;
      --r2: 28px;
    }

    * {
      box-sizing: border-box
    }

    body {
      margin: 0;
      font-family: system-ui, Segoe UI, Arial;
      color: var(--text);
      background:
        radial-gradient(1200px 650px at 50% -260px, rgba(214, 181, 74, .26), transparent 60%),
        radial-gradient(900px 580px at 88% 18%, rgba(214, 181, 74, .14), transparent 60%),
        radial-gradient(900px 580px at 16% 28%, rgba(255, 255, 255, .06), transparent 60%),
        var(--bg);
      overflow-x: hidden;
    }

    .wrap {
      max-width: 1220px;
      margin: 0 auto;
      padding: 22px 16px 76px
    }

    /* ===== HERO (mirip gambar) ===== */
    .hero {
      position: relative;
      border-radius: var(--r2);
      padding: 22px 22px 18px;
      border: 1px solid rgba(214, 181, 74, .20);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, .06), rgba(255, 255, 255, .02)),
        radial-gradient(900px 420px at 50% 0%, rgba(214, 181, 74, .26), transparent 70%);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    /* garis emas atas/bawah seperti banner */
    .hero .goldTop,
    .hero .goldBottom {
      position: absolute;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--goldLine), transparent);
      opacity: .9;
    }

    .hero .goldTop {
      top: 0
    }

    .hero .goldBottom {
      bottom: 0
    }

    /* glow strip di tengah (mirip highlight) */
    .hero:before {
      content: "";
      position: absolute;
      inset: -2px;
      background:
        radial-gradient(700px 240px at 50% 0%, rgba(214, 181, 74, .30), transparent 72%),
        linear-gradient(90deg, transparent, rgba(214, 181, 74, .20), transparent);
      opacity: .40;
      pointer-events: none;
    }

    /* wave kanan seperti gambar (dibuat via SVG embedded) */
    .hero .wave {
      position: absolute;
      right: -30px;
      top: 78px;
      width: 520px;
      height: 260px;
      opacity: .55;
      filter: blur(.0px);
      pointer-events: none;
      mix-blend-mode: screen;
    }

    .heroTop {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding-top: 4px;
    }

    .logoBadge {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba(214, 181, 74, .08), rgba(214, 181, 74, .03));
      border: 1px solid rgba(214, 181, 74, .25);
      box-shadow: 0 8px 32px rgba(0, 0, 0, .3), inset 0 1px 0 rgba(255, 255, 255, .08);
      overflow: hidden;
      flex-shrink: 0;
      animation: logoFadeIn 0.6s ease-out;
    }

    @keyframes logoFadeIn {
      from {
        opacity: 0;
        transform: scale(0.95);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    .logoBadge img {
      width: 90%;
      height: 90%;
      object-fit: contain;
      opacity: 1;
      transition: opacity 0.3s ease;
    }

    .logoBadge img.loading {
      opacity: 0.5;
    }

    .logoFallback {
      display: none;
      width: 100%;
      height: 100%;
      align-items: center;
      justify-content: center;
      color: var(--gold);
      font-size: 32px;
      font-weight: 700;
      letter-spacing: 2px;
      background: linear-gradient(135deg, rgba(214, 181, 74, .12), rgba(214, 181, 74, .05));
    }

    .brand {
      text-align: center;
      line-height: 1.05
    }

    .brand .name {
      font-weight: 950;
      letter-spacing: .6px;
      color: var(--gold);
      font-size: 26px
    }

    .brand .tag {
      font-size: 12px;
      letter-spacing: 1.6px;
      text-transform: uppercase;
      color: rgba(255, 255, 255, .70)
    }

    .heroTitle {
      position: relative;
      margin: 14px 0 4px;
      text-align: center;
      font-weight: 980;
      font-size: 36px;
      letter-spacing: .2px;
    }

    .heroSub {
      text-align: center;
      margin: 0 0 14px;
      color: rgba(255, 255, 255, .76);
      font-size: 12.5px;
    }

    .heroForm {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 6px;
    }

    .inp {
      width: min(820px, 95vw);
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, .12);
      background: rgba(0, 0, 0, .28);
      color: #fff;
      outline: none;
      box-shadow: var(--inner);
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      border-radius: 14px;
      border: 1px solid rgba(214, 181, 74, .35);
      background: linear-gradient(180deg, #e6c86a, #b98b0f);
      color: #141414;
      font-weight: 950;
      cursor: pointer;
      box-shadow: 0 16px 46px rgba(214, 181, 74, .22);
      user-select: none;
    }

    .btn:disabled,
    .btn.isLoading {
      opacity: .86;
      cursor: progress;
      transform: none;
    }

    .btn .btnLabel {
      white-space: nowrap;
    }

    .btn .btnSpinner {
      width: 16px;
      height: 16px;
      border-radius: 999px;
      border: 2px solid rgba(20, 20, 20, .28);
      border-top-color: rgba(20, 20, 20, .9);
      animation: spin .75s linear infinite;
      display: none;
    }

    .btn.isLoading .btnSpinner {
      display: inline-flex;
    }

    .submitLoadingOverlay {
      position: fixed;
      inset: 0;
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      opacity: 0;
      pointer-events: none;
      transition: opacity .18s ease;
      background: rgba(5, 5, 8, .56);
      backdrop-filter: blur(2px);
    }

    body.is-submitting .submitLoadingOverlay {
      opacity: 1;
      pointer-events: auto;
    }

    .submitLoadingCard {
      width: min(560px, 94vw);
      border-radius: 18px;
      border: 1px solid rgba(214, 181, 74, .28);
      background: linear-gradient(180deg, var(--panelA), var(--panelB));
      box-shadow: var(--shadow);
      padding: 14px;
    }

    .submitLoadingTitle {
      color: rgba(255, 255, 255, .95);
      font-size: 16px;
      font-weight: 900;
      margin-bottom: 3px;
    }

    .submitLoadingSub {
      color: rgba(255, 255, 255, .72);
      font-size: 12px;
      margin-bottom: 12px;
    }

    .submitLoadingStepProgress {
      width: 100%;
      height: 8px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, .12);
      background: rgba(255, 255, 255, .06);
      overflow: hidden;
      margin-bottom: 8px;
    }

    .submitLoadingStepFill {
      width: 0%;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #e6c86a, #b98b0f);
      transition: width .24s ease;
    }

    .submitLoadingStepMeta {
      color: rgba(255, 255, 255, .78);
      font-size: 11px;
      margin-bottom: 8px;
    }

    .submitSkeletonLine {
      height: 11px;
      border-radius: 999px;
      margin-top: 8px;
      background: linear-gradient(90deg,
          rgba(255, 255, 255, .10) 20%,
          rgba(255, 255, 255, .26) 50%,
          rgba(255, 255, 255, .10) 80%);
      background-size: 220% 100%;
      animation: shimmer 1.1s linear infinite;
    }

    .submitSkeletonLine.w80 {
      width: 80%;
    }

    .submitSkeletonLine.w62 {
      width: 62%;
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }

    @keyframes shimmer {
      from {
        background-position: 100% 0;
      }

      to {
        background-position: -100% 0;
      }
    }

    .btn .g {
      width: 22px;
      height: 22px;
      border-radius: 7px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, .14);
      border: 1px solid rgba(0, 0, 0, .18);
      font-weight: 950;
    }

    .hint {
      width: 100%;
      text-align: center;
      color: rgba(255, 255, 255, .68);
      font-size: 12px;
      margin-top: 6px;
      line-height: 1.35;
    }

    .loadingEstimateTools {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 4px;
    }

    .loadingEstimateReset {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgba(255, 255, 255, .18);
      background: rgba(255, 255, 255, .04);
      color: rgba(255, 255, 255, .86);
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      line-height: 1.1;
    }

    .loadingEstimateReset:hover {
      border-color: rgba(214, 181, 74, .45);
      color: #fff;
      background: rgba(214, 181, 74, .14);
    }

    .loadingEstimateReset:disabled {
      opacity: .65;
      cursor: default;
    }

    .loadingEstimateInfo {
      font-size: 11px;
      color: rgba(255, 255, 255, .56);
    }

    .viewToggle {
      display: none;
      width: 100%;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }

    .toggleBtn {
      border: 1px solid rgba(255, 255, 255, .16);
      background: rgba(255, 255, 255, .04);
      color: rgba(255, 255, 255, .88);
      border-radius: 999px;
      padding: 7px 12px;
      font-size: 11.5px;
      font-weight: 700;
      cursor: pointer;
    }

    .toggleBtn[aria-pressed="true"] {
      border-color: rgba(214, 181, 74, .45);
      background: rgba(214, 181, 74, .2);
      color: #fff;
    }

    .toggleBtn.secondary {
      border-color: rgba(255, 255, 255, .14);
      background: rgba(255, 255, 255, .02);
      color: rgba(255, 255, 255, .76);
      font-weight: 600;
    }

    .err {
      margin: 10px auto 0;
      max-width: 980px;
      padding: 10px 12px;
      border-radius: 16px;
      border: 1px solid rgba(255, 0, 0, .28);
      background: rgba(255, 0, 0, .08);
    }

    /* ===== GRID ===== */
    .grid {
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 16px;
      grid-auto-flow: row dense;
    }

    .sectionTitle {
      grid-column: span 12;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 20px;
      font-weight: 950;
      color: rgba(255, 255, 255, .88);
      margin-top: 4px;
      margin-bottom: 2px;
    }

    .sectionTitle .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--gold);
      box-shadow: 0 0 0 4px rgba(214, 181, 74, .18);
    }

    .panel {
      position: relative;
      border-radius: var(--r);
      padding: 14px;
      border: 1px solid rgba(255, 255, 255, .10);
      background: linear-gradient(180deg, var(--panelA), var(--panelB));
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel.hintPanel {
      padding: 10px 12px;
      border-style: dashed;
      border-color: rgba(255, 255, 255, .14);
      background: rgba(255, 255, 255, .02);
    }

    .panel.hintPanel .mini {
      font-size: 11.5px;
      color: rgba(255, 255, 255, .68);
    }

    /* highlight kanan atas panel seperti gambar */
    .panel:after {
      content: "";
      position: absolute;
      inset: -2px;
      background: radial-gradient(420px 170px at 82% 0%, rgba(214, 181, 74, .16), transparent 70%);
      opacity: .70;
      pointer-events: none;
    }

    .panel.gold {
      border: 1px solid rgba(214, 181, 74, .18);
      box-shadow: var(--shadow), var(--glow);
    }

    .panel h3 {
      position: relative;
      margin: 0 0 10px;
      font-size: 16px;
      font-weight: 950;
      color: rgba(255, 255, 255, .90);
      line-height: 1.25;
    }

    .mini {
      position: relative;
      color: var(--muted);
      font-size: 12.5px
    }

    .segContext {
      font-weight: 700;
      letter-spacing: .1px;
      transition: color .18s ease;
    }

    .segContext.all {
      color: rgba(214, 181, 74, .92);
    }

    .segContext.used {
      color: rgba(111, 219, 146, .92);
    }

    .segContext.non_user {
      color: rgba(128, 198, 255, .92);
    }

    /* ===== KPI ===== */
    .kpi {
      grid-column: span 4;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
    }

    .kpiSimple {
      grid-column: span 6;
    }

    .kpiDetail {
      grid-column: span 12;
      align-items: flex-start;
    }

    .kpiDetail .spark {
      display: none;
    }

    .kpi .ico {
      width: 40px;
      height: 40px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(214, 181, 74, .10);
      border: 1px solid rgba(214, 181, 74, .22);
      color: var(--gold);
      font-weight: 950;
      flex: 0 0 auto;
    }

    .kpi .label {
      font-size: 12px;
      color: rgba(255, 255, 255, .72)
    }

    .kpi .value {
      margin-top: 2px;
      font-size: 28px;
      font-weight: 980
    }

    .kpiMain {
      min-width: 0;
      display: grid;
      gap: 2px;
    }

    .kpiMeta {
      margin-top: 4px;
      color: rgba(255, 140, 140, .95);
      font-size: 11.5px;
      line-height: 1.35;
    }

    .kpiReadiness {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 6px;
    }

    .kpiReadinessMeta {
      color: rgba(255, 255, 255, .82);
      font-size: 11.5px;
      font-weight: 800;
    }

    .kpi .spark {
      margin-left: auto;
      width: 62px;
      height: 16px;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(214, 181, 74, 0), rgba(214, 181, 74, .65), rgba(214, 181, 74, .10));
      opacity: .95;
    }

    .mlStats {
      margin-top: 8px;
      display: grid;
      gap: 4px;
      line-height: 1.35;
    }

    .mlStats .modelLine {
      color: rgba(255, 255, 255, .88);
    }

    .mlStats .metricRow {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 6px;
    }

    .mlStats .metricName {
      min-width: 132px;
      color: rgba(255, 255, 255, .90);
      font-weight: 800;
    }

    .mlStats .metricPair {
      white-space: nowrap;
    }

    .mlStats .sep {
      color: rgba(255, 255, 255, .35);
    }

    .kpiSimple .kpiMain {
      gap: 1px;
    }

    /* ===== ABSA ANALYSIS ===== */
    .absa {
      grid-column: span 7
    }

    .absaGrid {
      display: grid;
      grid-template-columns: 1.25fr .75fr;
      gap: 14px
    }

    .cm {
      display: grid;
      grid-template-columns: 84px 1fr 1fr;
      gap: 10px;
      align-items: center;
      margin-top: 8px;
    }

    .axis {
      color: rgba(255, 255, 255, .70);
      font-size: 12px;
      writing-mode: vertical-rl;
      transform: rotate(180deg);
      text-align: center;
      padding: 6px 0;
    }

    .colhdr {
      color: rgba(255, 255, 255, .70);
      font-size: 12px;
      text-align: center;
      padding-bottom: 6px
    }

    .mat {
      grid-column: 2 / 4;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .cell {
      border-radius: 16px;
      min-height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      font-weight: 980;
      border: 1px solid rgba(255, 255, 255, .10);
      box-shadow: var(--inner);
    }

    .c1 {
      background: linear-gradient(180deg, rgba(71, 180, 105, .46), rgba(71, 180, 105, .16))
    }

    .c2 {
      background: linear-gradient(180deg, rgba(225, 179, 55, .58), rgba(225, 179, 55, .18))
    }

    .c3 {
      background: linear-gradient(180deg, rgba(215, 92, 68, .58), rgba(215, 92, 68, .18))
    }

    .c4 {
      background: linear-gradient(180deg, rgba(140, 140, 150, .36), rgba(140, 140, 150, .12))
    }

    .legend {
      margin-top: 10px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 11.5px;
      color: rgba(255, 255, 255, .78)
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, .03);
      border: 1px solid rgba(255, 255, 255, .08);
      box-shadow: var(--inner);
    }

    .sw {
      width: 10px;
      height: 10px;
      border-radius: 3px
    }

    .sw.g {
      background: rgba(71, 180, 105, .85)
    }

    .sw.y {
      background: rgba(225, 179, 55, .92)
    }

    .sw.r {
      background: rgba(215, 92, 68, .92)
    }

    .sw.n {
      background: rgba(140, 140, 150, .75)
    }

    /* chips top kata: lebih mirip (rapat) */
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px
    }

    .chip {
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, .03);
      border: 1px solid rgba(255, 255, 255, .08);
      box-shadow: var(--inner);
      font-size: 12px;
      min-width: 120px;
    }

    .chip b {
      font-weight: 980
    }

    /* ===== SENTIM PER ASPEK ===== */
    .sentim {
      grid-column: span 5
    }

    .donutWrap {
      display: flex;
      gap: 14px;
      align-items: center
    }

    .donut {
      width: 170px;
      height: 170px;
      border-radius: 999px;
      background: conic-gradient(var(--gold) 0 var(--pct), rgba(255, 255, 255, .11) var(--pct) 100%);
      position: relative;
      border: 1px solid rgba(214, 181, 74, .18);
      box-shadow: var(--glow);
      flex: 0 0 auto;
    }

    .donut:before {
      content: "";
      position: absolute;
      inset: 16px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(0, 0, 0, .75), rgba(0, 0, 0, .35));
      border: 1px solid rgba(255, 255, 255, .06);
      box-shadow: var(--inner);
    }

    .donut .pctTxt {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 980;
      font-size: 34px;
      color: rgba(255, 255, 255, .92);
    }

    .breakdown {
      flex: 1
    }

    .brow {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 7px 0;
      border-bottom: 1px solid rgba(255, 255, 255, .06)
    }

    .brow:last-child {
      border-bottom: 0
    }

    .brow .k {
      color: rgba(255, 255, 255, .75);
      font-size: 12px
    }

    .brow .v {
      color: rgba(255, 255, 255, .92);
      font-weight: 980;
      font-size: 12px
    }

    .miniBars {
      margin-top: 12px
    }

    .barRow {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 10px 0
    }

    .barRow .name {
      width: 84px;
      color: rgba(255, 255, 255, .72);
      font-size: 12px
    }

    .bar {
      flex: 1;
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, .08);
      border: 1px solid rgba(255, 255, 255, .06);
      overflow: hidden;
      box-shadow: var(--inner);
    }

    .fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--gold), rgba(214, 181, 74, .18));
    }

    .barRow .p {
      width: 42px;
      text-align: right;
      color: rgba(255, 255, 255, .82);
      font-size: 12px;
      font-weight: 980
    }

    /* ===== TOP ISU + REKOM ===== */
    .isu {
      grid-column: span 7
    }

    .rekom {
      grid-column: span 5
    }

    table {
      width: 100%;
      border-collapse: collapse
    }

    .tableScrollX {
      width: 100%;
      overflow-x: auto;
      overflow-y: hidden;
      -webkit-overflow-scrolling: touch;
      touch-action: pan-x;
      scroll-behavior: smooth;
      scroll-padding-inline: 10px;
      overscroll-behavior-x: contain;
      scrollbar-width: thin;
      scrollbar-color: rgba(214, 181, 74, .45) rgba(255, 255, 255, .07);
      position: relative;
    }

    .tableScrollX.can-scroll::before,
    .tableScrollX.can-scroll::after {
      content: "";
      position: absolute;
      top: 0;
      bottom: 0;
      width: 18px;
      pointer-events: none;
      opacity: 0;
      transition: opacity .16s ease;
      z-index: 3;
    }

    .tableScrollX.can-scroll::before {
      left: 0;
      background: linear-gradient(90deg, rgba(5, 5, 8, .68), rgba(5, 5, 8, 0));
    }

    .tableScrollX.can-scroll::after {
      right: 0;
      background: linear-gradient(270deg, rgba(5, 5, 8, .68), rgba(5, 5, 8, 0));
    }

    .tableScrollX.can-scroll.show-left::before {
      opacity: 1;
    }

    .tableScrollX.can-scroll.show-right::after {
      opacity: 1;
    }

    .tableScrollX::-webkit-scrollbar {
      height: 6px;
    }

    .tableScrollX::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, .06);
      border-radius: 999px;
    }

    .tableScrollX::-webkit-scrollbar-thumb {
      background: rgba(214, 181, 74, .42);
      border-radius: 999px;
    }

    .tableScrollX>table {
      margin: 0;
      min-width: 100%;
      border-collapse: separate;
      border-spacing: 0;
    }

    .tableScrollX>table th:first-child,
    .tableScrollX>table td:first-child {
      padding-left: 12px;
    }

    .tableScrollX>table th:last-child,
    .tableScrollX>table td:last-child {
      padding-right: 12px;
    }

    .tableScrollX table {
      font-variant-numeric: tabular-nums;
    }

    .tableScrollX.variantRankScroll {
      border: 1px solid rgba(214, 220, 228, .22);
      border-radius: 10px;
      background: rgba(8, 11, 18, .58);
      padding-bottom: 4px;
    }

    .tableScrollX.variantRankScroll.can-scroll::before,
    .tableScrollX.variantRankScroll.can-scroll::after {
      display: none;
    }

    th,
    td {
      padding: 11px 10px;
      border-bottom: 1px solid rgba(255, 255, 255, .08)
    }

    th {
      color: var(--gold);
      font-size: 12.5px;
      text-align: left;
      background: rgba(255, 255, 255, .02)
    }

    td {
      color: rgba(255, 255, 255, .92);
      font-size: 13px
    }

    .quickRecoText {
      display: block;
      max-width: 520px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .healthAlertTable,
    .earlyWarnTable {
      table-layout: fixed;
    }

    .healthAlertTable th:nth-child(1),
    .healthAlertTable td:nth-child(1) {
      width: 20%;
    }

    .healthAlertTable th:nth-child(2),
    .healthAlertTable td:nth-child(2),
    .earlyWarnTable th:nth-child(1),
    .earlyWarnTable td:nth-child(1) {
      width: 18%;
    }

    .healthAlertTable th:nth-child(3),
    .healthAlertTable td:nth-child(3),
    .earlyWarnTable th:nth-child(3),
    .earlyWarnTable td:nth-child(3) {
      width: 16%;
      white-space: nowrap;
      text-align: right;
    }

    .earlyWarnTable th:nth-child(2),
    .earlyWarnTable td:nth-child(2) {
      width: 22%;
    }

    .healthAlertTable td,
    .earlyWarnTable td {
      vertical-align: top;
    }

    .healthAlertTable .quickRecoText,
    .earlyWarnTable .quickRecoText {
      max-width: 100%;
      white-space: normal;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .trendTable th:nth-child(2),
    .trendTable td:nth-child(2),
    .trendTable th:nth-child(3),
    .trendTable td:nth-child(3),
    .trendTable th:nth-child(4),
    .trendTable td:nth-child(4),
    .segmentCompareTable th:nth-child(2),
    .segmentCompareTable td:nth-child(2),
    .segmentCompareTable th:nth-child(3),
    .segmentCompareTable td:nth-child(3),
    .topIsuTable th:nth-child(3),
    .topIsuTable td:nth-child(3),
    .variantRankTable th:nth-child(1),
    .variantRankTable td:nth-child(1),
    .variantRankTable th:nth-child(3),
    .variantRankTable td:nth-child(3),
    .variantRankTable th:nth-child(4),
    .variantRankTable td:nth-child(4),
    .variantRankTable th:nth-child(5),
    .variantRankTable td:nth-child(5) {
      text-align: right;
      white-space: nowrap;
    }

    .variantRankTable {
      min-width: 760px;
      table-layout: fixed;
      border: 0;
      border-radius: 0;
      overflow: visible;
      background: transparent;
    }

    .variantRankTable th,
    .variantRankTable td {
      padding: 8px 8px;
      line-height: 1.28;
    }

    .variantRankTable thead th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: rgba(32, 40, 54, .96);
      color: rgba(247, 249, 252, .98);
      border-bottom: 1px solid rgba(214, 220, 228, .35);
      font-size: 12px;
    }

    .variantRankTable tbody tr:nth-child(odd) td {
      background: rgba(251, 252, 253, .02);
    }

    .variantRankTable tbody tr:nth-child(even) td {
      background: rgba(246, 248, 251, .045);
    }

    .variantRankTable th:nth-child(1),
    .variantRankTable td:nth-child(1) {
      width: 52px;
    }

    .variantRankTable th:nth-child(2),
    .variantRankTable td:nth-child(2) {
      width: 182px;
      white-space: normal;
      word-break: break-word;
    }

    .variantRankTable th:nth-child(3),
    .variantRankTable td:nth-child(3),
    .variantRankTable th:nth-child(4),
    .variantRankTable td:nth-child(4),
    .variantRankTable th:nth-child(5),
    .variantRankTable td:nth-child(5) {
      width: 92px;
    }

    .variantRankTable th:nth-child(6),
    .variantRankTable td:nth-child(6) {
      width: 132px;
    }

    .variantRankTable th:nth-child(7),
    .variantRankTable td:nth-child(7) {
      min-width: 220px;
      width: 240px;
    }

    .variantIsuText {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      white-space: normal;
      word-break: break-word;
      max-width: 100%;
    }

    .trendTable {
      min-width: 620px;
    }

    .segmentCompareTable {
      min-width: 740px;
      table-layout: fixed;
    }

    .segmentCompareTable th {
      white-space: normal;
      line-height: 1.28;
    }

    .topIsuTable {
      min-width: 620px;
      table-layout: fixed;
    }

    .topIsuTable th:nth-child(2),
    .topIsuTable td:nth-child(2) {
      min-width: 220px;
      white-space: normal;
      word-break: break-word;
    }

    .segmentSummaryTable th,
    .segmentSummaryTable td {
      text-align: right;
      white-space: nowrap;
    }

    .alignBadge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 82px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, .16);
      font-size: 10.5px;
      font-weight: 900;
      letter-spacing: .22px;
      text-transform: uppercase;
      line-height: 1.1;
    }

    .alignBadge.aligned {
      color: rgba(71, 180, 105, .96);
      background: rgba(71, 180, 105, .12);
      border-color: rgba(71, 180, 105, .36);
    }

    .alignBadge.partial {
      color: rgba(225, 179, 55, .98);
      background: rgba(225, 179, 55, .14);
      border-color: rgba(225, 179, 55, .38);
    }

    .alignBadge.diverged {
      color: rgba(215, 92, 68, .97);
      background: rgba(215, 92, 68, .13);
      border-color: rgba(215, 92, 68, .38);
    }

    .variantSyncHint {
      margin-top: 8px;
      margin-bottom: 6px;
      color: rgba(255, 255, 255, .72);
      font-size: 11px;
      line-height: 1.45;
    }

    .rekomItem {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      padding: 12px;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, .08);
      background: rgba(255, 255, 255, .03);
      margin-top: 10px;
      box-shadow: var(--inner);
    }

    .rekomItem:first-of-type {
      margin-top: 8px
    }

    .ricon {
      width: 40px;
      height: 40px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(214, 181, 74, .10);
      border: 1px solid rgba(214, 181, 74, .22);
      color: var(--gold);
      font-weight: 980;
      flex: 0 0 auto;
    }

    .ttl {
      margin: 0 0 4px;
      font-weight: 980;
      color: var(--gold);
      font-size: 13px
    }

    .txt {
      margin: 0;
      color: rgba(255, 255, 255, .84);
      font-size: 12px;
      line-height: 1.45
    }

    .segCtl {
      grid-column: span 12;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .segBtns {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .segBtn {
      border: 1px solid rgba(255, 255, 255, .14);
      background: rgba(255, 255, 255, .03);
      color: rgba(255, 255, 255, .88);
      border-radius: 999px;
      padding: 7px 12px;
      font-size: 12px;
      cursor: pointer;
    }

    .segBtn.active {
      border-color: rgba(214, 181, 74, .42);
      background: rgba(214, 181, 74, .18);
      color: #fff;
    }

    .opsReadiness {
      grid-column: span 12;
    }

    .opsReadinessHead {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }

    .opsReadinessScore {
      color: rgba(255, 255, 255, .86);
      font-size: 12px;
      font-weight: 800;
    }

    .opsReadinessGrid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 8px;
    }

    .opsReadinessBox {
      border: 1px solid rgba(255, 255, 255, .12);
      border-radius: 12px;
      padding: 10px 11px;
      background: rgba(255, 255, 255, .03);
    }

    .opsReadinessBox .mini {
      color: rgba(255, 255, 255, .72);
      font-size: 11.5px;
      margin-top: 2px;
    }

    .opsReadinessTitle {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 12px;
      font-weight: 850;
      color: rgba(255, 255, 255, .90);
    }

    .opsWarnings {
      margin: 7px 0 0;
      padding-left: 18px;
      color: rgba(255, 255, 255, .83);
      font-size: 12px;
      line-height: 1.45;
    }

    .opsWarnings li {
      margin: 4px 0;
    }

    .rekomHead {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 6px;
    }

    .rekomActions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .miniActionBtn {
      border: 1px solid rgba(214, 181, 74, .35);
      background: rgba(214, 181, 74, .12);
      color: rgba(255, 255, 255, .92);
      border-radius: 999px;
      padding: 7px 12px;
      font-size: 11.5px;
      font-weight: 800;
      cursor: pointer;
    }

    .miniActionBtn:hover {
      background: rgba(214, 181, 74, .18);
    }

    .miniActionBtn.secondary {
      border-color: rgba(255, 255, 255, .22);
      background: rgba(255, 255, 255, .05);
    }

    .miniActionBtn.secondary:hover {
      background: rgba(255, 255, 255, .12);
    }

    .inp:focus-visible,
    .btn:focus-visible,
    .segBtn:focus-visible,
    .toggleBtn:focus-visible,
    .miniActionBtn:focus-visible,
    .loadingEstimateReset:focus-visible,
    .backTopBtn:focus-visible {
      outline: 2px solid rgba(214, 181, 74, .72);
      outline-offset: 2px;
    }

    .drill {
      grid-column: span 12;
    }

    .drillGrid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .drillBox {
      border: 1px solid rgba(255, 255, 255, .08);
      border-radius: 14px;
      padding: 10px;
      background: rgba(255, 255, 255, .02);
    }

    .drillBox h4 {
      margin: 0 0 8px;
      font-size: 13px;
      color: var(--gold);
    }

    .drillCount {
      margin-left: 6px;
      color: rgba(255, 255, 255, .72);
      font-size: 11px;
      font-weight: 700;
    }

    .drillList {
      margin: 0;
      padding-left: 18px;
      color: rgba(255, 255, 255, .85);
      font-size: 12px;
      line-height: 1.45;
    }

    .drillList li {
      margin: 6px 0;
    }

    .intentBadge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 68px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 900;
      letter-spacing: .2px;
      line-height: 1.1;
      text-transform: uppercase;
      border: 1px solid rgba(255, 255, 255, .16);
    }

    .intentBadge.high {
      color: rgba(71, 180, 105, .95);
      background: rgba(71, 180, 105, .12);
      border-color: rgba(71, 180, 105, .35);
    }

    .intentBadge.medium {
      color: rgba(225, 179, 55, .96);
      background: rgba(225, 179, 55, .14);
      border-color: rgba(225, 179, 55, .38);
    }

    .intentBadge.low {
      color: rgba(215, 92, 68, .96);
      background: rgba(215, 92, 68, .14);
      border-color: rgba(215, 92, 68, .38);
    }

    /* ===== PRIORITAS ===== */
    .prio {
      grid-column: span 12
    }

    .prioRow {
      display: grid;
      grid-template-columns: 120px 1fr 52px;
      gap: 12px;
      align-items: center;
      margin: 12px 0;
    }

    .prioRow .nm {
      color: rgba(255, 255, 255, .84);
      font-weight: 850
    }

    .prioBar {
      height: 16px;
      border-radius: 999px;
      background: rgba(255, 255, 255, .08);
      border: 1px solid rgba(255, 255, 255, .06);
      overflow: hidden;
      box-shadow: var(--inner);
    }

    .prioFill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #e6c86a, #b98b0f)
    }

    .prioVal {
      text-align: right;
      color: rgba(255, 255, 255, .92);
      font-weight: 980
    }

    .backTopBtn {
      position: fixed;
      right: 18px;
      bottom: 20px;
      width: 42px;
      height: 42px;
      border-radius: 999px;
      border: 1px solid rgba(214, 181, 74, .45);
      background: linear-gradient(180deg, rgba(230, 200, 106, .94), rgba(185, 139, 15, .94));
      color: #171717;
      font-size: 20px;
      font-weight: 980;
      line-height: 1;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(0, 0, 0, .38);
      opacity: 0;
      pointer-events: none;
      transform: translateY(10px);
      transition: opacity .2s ease, transform .2s ease;
      z-index: 900;
    }

    .backTopBtn.show {
      opacity: .95;
      pointer-events: auto;
      transform: translateY(0);
    }

    .backTopBtn:hover {
      opacity: 1;
      transform: translateY(-1px);
    }

    @media (prefers-reduced-motion: reduce) {

      .btn .btnSpinner,
      .submitSkeletonLine {
        animation: none;
      }

      .submitLoadingStepFill,
      .submitLoadingOverlay,
      .backTopBtn {
        transition: none;
      }
    }

    @media (max-width:1100px) {
      .wrap {
        padding: 16px 12px 56px;
      }

      .hero {
        padding: 18px 16px 14px;
      }

      .absa {
        grid-column: span 12
      }

      .sentim {
        grid-column: span 12
      }

      .isu {
        grid-column: span 12
      }

      .rekom {
        grid-column: span 12
      }

      .absaGrid {
        grid-template-columns: 1fr;
      }

      .panel {
        padding: 11px;
      }
    }

    @media (max-width:900px) {
      .viewToggle {
        display: flex;
      }

      .grid {
        gap: 10px;
      }

      .heroTitle {
        font-size: 30px;
      }

      .kpi .value {
        font-size: 24px;
      }

      .cm {
        grid-template-columns: 62px 1fr 1fr;
        gap: 8px;
      }

      .cell {
        min-height: 56px;
        font-size: 22px;
      }

      .donut {
        width: 150px;
        height: 150px;
      }

      .donut .pctTxt {
        font-size: 29px;
      }

      .prioRow {
        grid-template-columns: 96px 1fr 44px;
        gap: 10px;
      }

      .segBtns {
        width: 100%;
      }

      .segBtn {
        flex: 1 1 calc(50% - 8px);
        text-align: center;
      }

      .opsReadinessGrid {
        grid-template-columns: 1fr;
      }

      .rekomHead {
        align-items: flex-start;
      }

      .rekomActions {
        width: 100%;
      }

      .miniActionBtn {
        flex: 1 1 100%;
        text-align: center;
      }

      body.mobile-compact .wrap {
        padding-top: 10px;
      }

      body.mobile-compact .hero {
        padding: 12px 10px 10px;
      }

      body.mobile-compact .heroTitle {
        font-size: 24px;
      }

      body.mobile-compact .heroSub {
        font-size: 11px;
      }

      body.mobile-compact .panel {
        padding: 9px;
      }

      body.mobile-compact .panel h3 {
        font-size: 13.5px;
        margin-bottom: 7px;
      }

      body.mobile-compact .kpi {
        padding: 9px 10px;
        gap: 8px;
      }

      body.mobile-compact .kpi .ico {
        width: 30px;
        height: 30px;
      }

      body.mobile-compact .kpi .label,
      body.mobile-compact .mini {
        font-size: 11px;
      }

      body.mobile-compact .kpi .value {
        font-size: 19px;
      }

      body.mobile-compact .donut {
        width: 114px;
        height: 114px;
      }

      body.mobile-compact .donut .pctTxt {
        font-size: 20px;
      }

      body.mobile-compact th,
      body.mobile-compact td {
        padding: 7px 6px;
      }

      body.mobile-compact td {
        font-size: 11.5px;
      }

      body.mobile-compact .chip {
        min-width: 84px;
        padding: 6px 8px;
      }

      body.mobile-compact .rekomItem {
        padding: 8px;
        gap: 8px;
      }

      body.mobile-compact .ricon {
        width: 28px;
        height: 28px;
      }
    }

    @media (max-width:768px) {
      #healthScopedArea {
        overflow: visible;
      }

      .tableScrollX {
        margin-inline: -4px;
        padding-inline: 4px;
      }

      #healthScopedArea .tableScrollX {
        overflow-x: auto;
        overflow-y: hidden;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        scrollbar-color: rgba(214, 181, 74, .45) rgba(255, 255, 255, .07);
        padding-bottom: 4px;
      }

      #healthScopedArea .tableScrollX::-webkit-scrollbar {
        height: 6px;
      }

      #healthScopedArea .tableScrollX::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, .06);
        border-radius: 999px;
      }

      #healthScopedArea .tableScrollX::-webkit-scrollbar-thumb {
        background: rgba(214, 181, 74, .42);
        border-radius: 999px;
      }

      .hero .wave {
        display: none;
      }

      .heroForm {
        gap: 8px;
      }

      .inp {
        width: 100%;
        min-width: 0;
      }

      .btn {
        width: 100%;
        justify-content: center;
      }

      .sectionTitle {
        font-size: 18px;
      }

      .drillGrid {
        grid-template-columns: 1fr;
      }

      .rekomItem {
        padding: 10px;
      }

      .ricon {
        width: 34px;
        height: 34px;
      }

      table {
        display: table;
        width: 100%;
      }

      .tableScrollX>table {
        display: table;
        width: max-content;
        min-width: 100%;
        overflow: visible;
      }

      .tableScrollX.can-scroll::before,
      .tableScrollX.can-scroll::after {
        width: 10px;
      }

      th,
      td {
        white-space: nowrap;
        word-break: normal;
        line-height: 1.35;
        vertical-align: top;
      }

      .healthAlertTable,
      .earlyWarnTable {
        min-width: 640px;
        table-layout: fixed;
      }

      .healthAlertTable th,
      .healthAlertTable td,
      .earlyWarnTable th,
      .earlyWarnTable td {
        padding: 8px 6px;
        font-size: 11.2px;
        line-height: 1.35;
      }

      .healthAlertTable th:nth-child(1),
      .healthAlertTable td:nth-child(1) {
        width: 18%;
      }

      .healthAlertTable th:nth-child(2),
      .healthAlertTable td:nth-child(2),
      .earlyWarnTable th:nth-child(1),
      .earlyWarnTable td:nth-child(1) {
        width: 16%;
      }

      .healthAlertTable th:nth-child(3),
      .healthAlertTable td:nth-child(3),
      .earlyWarnTable th:nth-child(3),
      .earlyWarnTable td:nth-child(3) {
        width: 14%;
      }

      .earlyWarnTable th:nth-child(2),
      .earlyWarnTable td:nth-child(2) {
        width: 20%;
      }

      #healthScopedArea .tableScrollX+.tableScrollX {
        margin-top: 6px;
      }

      .trendTable,
      .segmentCompareTable,
      .topIsuTable,
      .variantRankTable,
      .segmentSummaryTable {
        min-width: 620px;
      }

      .variantRankTable {
        min-width: 700px;
        table-layout: auto;
      }

      .variantRankTable thead th {
        position: static;
      }

      .variantRankTable th,
      .variantRankTable td {
        padding: 7px 6px;
        font-size: 11px;
        line-height: 1.3;
      }

      .variantRankTable th:nth-child(1),
      .variantRankTable td:nth-child(1) {
        width: 44px;
      }

      .variantRankTable th:nth-child(2),
      .variantRankTable td:nth-child(2) {
        width: 160px;
      }

      .variantRankTable th:nth-child(3),
      .variantRankTable td:nth-child(3),
      .variantRankTable th:nth-child(4),
      .variantRankTable td:nth-child(4),
      .variantRankTable th:nth-child(5),
      .variantRankTable td:nth-child(5) {
        width: 78px;
      }

      .variantRankTable th:nth-child(6),
      .variantRankTable td:nth-child(6) {
        width: 108px;
      }

      .variantRankTable th:nth-child(7),
      .variantRankTable td:nth-child(7) {
        min-width: 186px;
        width: 206px;
      }

      .variantRankTable .alignBadge {
        min-width: 72px;
        font-size: 10px;
        padding: 3px 8px;
      }

      .quickRecoText {
        white-space: normal;
        min-width: 180px;
        line-height: 1.4;
      }

      .healthAlertTable td:nth-child(4),
      .earlyWarnTable td:nth-child(4) {
        min-width: 208px;
      }

      .healthAlertTable .quickRecoText,
      .earlyWarnTable .quickRecoText {
        -webkit-line-clamp: 3;
      }

      .segBtn {
        flex: 1 1 100%;
      }
    }

    @media (max-width:640px) {
      .wrap {
        padding: 12px 10px 44px;
      }

      .tableScrollX {
        margin-inline: -3px;
        padding-inline: 3px;
      }

      .tableScrollX.can-scroll::before,
      .tableScrollX.can-scroll::after {
        display: none;
      }

      .backTopBtn {
        right: 12px;
        bottom: 14px;
        width: 38px;
        height: 38px;
        font-size: 18px;
      }

      .hero {
        border-radius: 20px;
        padding: 14px 12px 12px;
      }

      .kpi {
        grid-column: span 12
      }

      .kpi {
        padding: 10px 11px;
      }

      .kpi .ico {
        width: 34px;
        height: 34px;
      }

      .kpi .value {
        font-size: 22px;
      }

      .mlStats .metricName {
        min-width: 104px;
      }

      .heroTitle {
        font-size: 28px
      }

      .heroSub {
        font-size: 11.5px;
      }

      .donutWrap {
        flex-direction: column;
        align-items: flex-start
      }

      .donut {
        width: 132px;
        height: 132px;
      }

      .donut .pctTxt {
        font-size: 24px;
      }

      .quickRecoText {
        min-width: 160px;
        max-width: 100%;
        white-space: normal;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .healthAlertTable,
      .earlyWarnTable {
        min-width: 600px;
      }

      .trendTable,
      .segmentCompareTable,
      .topIsuTable,
      .variantRankTable,
      .segmentSummaryTable {
        min-width: 580px;
      }

      .healthAlertTable th,
      .healthAlertTable td {
        font-size: 11px;
        padding: 8px 6px;
      }

      .healthAlertTable th:nth-child(1),
      .healthAlertTable td:nth-child(1) {
        width: 16%;
      }

      .healthAlertTable th:nth-child(2),
      .healthAlertTable td:nth-child(2) {
        width: 14%;
      }

      .healthAlertTable th:nth-child(3),
      .healthAlertTable td:nth-child(3) {
        width: 12%;
        white-space: nowrap;
      }

      .toggleBtn {
        width: calc(50% - 4px);
        text-align: center;
      }

      .prioRow {
        grid-template-columns: 1fr;
        gap: 6px;
        margin: 10px 0;
      }

      .prioRow .nm,
      .prioVal {
        text-align: left;
      }

      .mini {
        font-size: 11.5px;
      }

      .kpiMeta {
        font-size: 11px;
      }

      td {
        font-size: 12px;
      }

      .panel h3 {
        font-size: 14px;
      }
    }

    @media (max-width:420px) {
      .heroTitle {
        font-size: 24px;
      }

      .brand .name {
        font-size: 22px;
      }

      .segBtn {
        padding: 7px 10px;
        font-size: 11px;
      }

      .chip {
        min-width: 96px;
        font-size: 11px;
      }

      .cell {
        min-height: 50px;
        font-size: 20px;
      }

      .axis,
      .colhdr {
        font-size: 11px;
      }

      .healthAlertTable,
      .earlyWarnTable {
        min-width: 580px;
      }

      .healthAlertTable th,
      .healthAlertTable td,
      .earlyWarnTable th,
      .earlyWarnTable td {
        font-size: 10.9px;
        padding: 7px 5px;
      }

      .healthAlertTable td:nth-child(4),
      .earlyWarnTable td:nth-child(4) {
        min-width: 190px;
      }

      .variantRankTable {
        min-width: 660px;
      }

      .variantRankTable th,
      .variantRankTable td {
        font-size: 10.6px;
        padding: 6px 5px;
      }

      .variantRankTable th:nth-child(2),
      .variantRankTable td:nth-child(2) {
        width: 154px;
      }

      .variantRankTable th:nth-child(7),
      .variantRankTable td:nth-child(7) {
        min-width: 176px;
        width: 188px;
      }

      .variantRankTable .alignBadge {
        min-width: 68px;
        font-size: 9.9px;
        padding: 3px 7px;
      }
    }

    @media (max-width:360px) {
      .wrap {
        padding: 10px 8px 38px;
      }

      .hero {
        padding: 12px 10px 10px;
        border-radius: 16px;
      }

      .heroTitle {
        font-size: 22px;
      }

      .heroSub {
        font-size: 11px;
        margin-bottom: 10px;
      }

      .btn,
      .inp {
        border-radius: 12px;
        padding: 10px 11px;
      }

      .sectionTitle {
        font-size: 16px;
      }

      .panel {
        padding: 9px;
        border-radius: 16px;
      }

      .panel h3 {
        font-size: 13.5px;
        margin-bottom: 7px;
      }

      .kpi {
        gap: 9px;
      }

      .kpiDetail {
        gap: 8px;
      }

      .kpiDetail .ico {
        width: 28px;
        height: 28px;
        border-radius: 10px;
      }

      .kpiDetail .label {
        font-size: 10.5px;
      }

      .kpiDetail .value {
        font-size: 18px;
      }

      .kpi .label {
        font-size: 11px;
      }

      .kpi .value {
        font-size: 20px;
      }

      .donut {
        width: 118px;
        height: 118px;
      }

      .donut .pctTxt {
        font-size: 22px;
      }

      .brow .k,
      .brow .v,
      .barRow .name,
      .barRow .p {
        font-size: 11px;
      }

      th,
      td {
        padding: 7px 6px;
      }

      td {
        font-size: 11.5px;
      }

      .chip {
        min-width: 88px;
        padding: 7px 8px;
      }

      .rekomItem {
        gap: 8px;
        padding: 8px;
      }

      .ricon {
        width: 30px;
        height: 30px;
        border-radius: 10px;
      }

      .ttl {
        font-size: 12px;
      }

      .txt,
      .drillList,
      .mini {
        font-size: 11px;
      }

      .mlStats .metricRow {
        gap: 4px;
      }

      .mlStats .metricName {
        font-size: 10.5px;
        min-width: 100%;
      }

      .mlStats .metricPair {
        white-space: normal;
      }

      .mlStats .sep {
        display: none;
      }

      .healthAlertTable th,
      .healthAlertTable td,
      .earlyWarnTable th,
      .earlyWarnTable td {
        font-size: 10.8px;
        padding: 7px 5px;
        line-height: 1.35;
      }

      .variantRankTable {
        min-width: 640px;
      }

      .variantRankTable th,
      .variantRankTable td {
        font-size: 10.4px;
        padding: 6px 5px;
      }

      .variantRankTable th:nth-child(2),
      .variantRankTable td:nth-child(2) {
        width: 150px;
      }

      .variantRankTable th:nth-child(7),
      .variantRankTable td:nth-child(7) {
        min-width: 172px;
        width: 182px;
      }

      .variantRankTable .alignBadge {
        min-width: 66px;
        font-size: 9.8px;
        padding: 3px 7px;
      }

      .healthAlertTable,
      .earlyWarnTable {
        min-width: 550px;
      }

      .healthAlertTable td:nth-child(4),
      .earlyWarnTable td:nth-child(4) {
        min-width: 176px;
        white-space: normal;
      }

      .intentBadge {
        min-width: 62px;
        font-size: 10px;
        padding: 3px 8px;
      }

      .healthAlertTable .quickRecoText,
      .earlyWarnTable .quickRecoText {
        -webkit-line-clamp: 3;
      }
    }

    @media (max-width:320px) {
      .heroTitle {
        font-size: 20px;
      }

      .brand .name {
        font-size: 20px;
      }

      .logoBadge {
        width: 46px;
        height: 46px;
      }

      .segBtn {
        padding: 6px 8px;
        font-size: 10.5px;
      }

      .cell {
        min-height: 44px;
        font-size: 18px;
      }

      .donut {
        width: 108px;
        height: 108px;
      }

      .donut .pctTxt {
        font-size: 20px;
      }

      .kpi .value {
        font-size: 18px;
      }

      .healthAlertTable,
      .earlyWarnTable {
        min-width: 510px;
      }

      .healthAlertTable th,
      .healthAlertTable td,
      .earlyWarnTable th,
      .earlyWarnTable td {
        font-size: 10.2px;
        padding: 6px 4px;
        line-height: 1.3;
      }

      .healthAlertTable td:nth-child(4),
      .earlyWarnTable td:nth-child(4) {
        min-width: 164px;
      }

      .healthAlertTable .quickRecoText,
      .earlyWarnTable .quickRecoText {
        -webkit-line-clamp: 3;
      }

      .variantRankTable {
        min-width: 600px;
      }

      .variantRankTable th,
      .variantRankTable td {
        font-size: 10.1px;
        padding: 5px 4px;
        line-height: 1.28;
      }

      .variantRankTable th:nth-child(2),
      .variantRankTable td:nth-child(2) {
        width: 146px;
      }

      .variantRankTable th:nth-child(7),
      .variantRankTable td:nth-child(7) {
        min-width: 164px;
        width: 174px;
      }

      .variantRankTable .alignBadge {
        min-width: 62px;
        font-size: 9.4px;
        padding: 3px 6px;
      }

      .intentBadge {
        min-width: 58px;
        font-size: 9.6px;
        padding: 3px 7px;
      }
    }
  </style>
</head>

<body>
  @php
    $kpi = data_get($result ?? [], 'kpi', []);
    $jumlahKomentar = data_get($kpi, 'jumlah_komentar');
    $akurasiModel = data_get($kpi, 'akurasi_model');
    $persenNegatif = data_get($kpi, 'persen_negatif');

    $akurasiText = is_numeric($akurasiModel) ? number_format($akurasiModel * 100, 1) . '%' : '—';
    $negatifText = is_numeric($persenNegatif) ? number_format($persenNegatif * 100, 1) . '%' : '—';

    // Confusion matrix - dari hasil analisis
    $cm = data_get($result ?? [], 'confusion_matrix', []);
    $tp = data_get($cm, 'tp', 0);
    $fp = data_get($cm, 'fp', 0);
    $fn = data_get($cm, 'fn', 0);
    $tn = data_get($cm, 'tn', 0);

    // Top kata - dari hasil analisis real
    $topKata = data_get($result ?? [], 'top_kata', []);

    // Sentimen per aspek - dari hasil analisis real
    $sentAspek = data_get($result ?? [], 'sentimen_per_aspek', []);

    // Donut chart: hitung persentase yang akan ditampilkan.
    // - Prioritas pertama: persen negatif
    // - Kalau tidak ada negatif (nilai = 0), gunakan persen positif agar chart tidak kosong
    $donutPct = 0;
    if (!empty($sentAspek)) {
      $first = $sentAspek[0];
      $pctNeg = (float) data_get($first, 'persen_negatif', 0);
      $total = (int) data_get($first, 'total', 0);
      $pctPos = $total > 0 ? round((data_get($first, 'positif', 0) / $total) * 100, 1) : 0;
      $donutPct = $pctNeg > 0 ? $pctNeg : $pctPos;
    }

    $topIsu = data_get($result ?? [], 'top_isu', []);
    $rekom = data_get($result ?? [], 'rekomendasi', []);
    $prio = data_get($result ?? [], 'prioritas', []);
    $variantAnalysis = data_get($result ?? [], 'variant_analysis', []);
    $variants = data_get($variantAnalysis, 'variants', []);
    $variantRecs = data_get($variantAnalysis, 'recommendations_by_variant', []);
    $variantRankings = data_get($variantAnalysis, 'rankings', []);
    $kemasanGlobalReco = data_get($variantAnalysis, 'kemasan_rekomendasi_global', 'Perkuat QC kemasan agar kualitas tetap konsisten.');
    $kemasanGlobalPlan = data_get($variantAnalysis, 'kemasan_plan_global', []);
    $defaultVariant = !empty($variants) ? $variants[0] : null;
    $defaultAromaReco = $defaultVariant ? data_get($variantRecs, $defaultVariant . '.aroma', '-') : '-';
    $defaultKetahananReco = $defaultVariant ? data_get($variantRecs, $defaultVariant . '.ketahanan', '-') : '-';
    $defaultAromaPlan = $defaultVariant ? data_get($variantRecs, $defaultVariant . '.aroma_plan', []) : [];
    $defaultKetahananPlan = $defaultVariant ? data_get($variantRecs, $defaultVariant . '.ketahanan_plan', []) : [];
    $confidenceLabelMap = [
      'high' => 'Tinggi',
      'medium' => 'Sedang',
      'low' => 'Rendah',
    ];
    $toConfidenceLabel = function ($value) use ($confidenceLabelMap) {
      $key = strtolower(trim((string) $value));
      return data_get($confidenceLabelMap, $key, '-');
    };
    $defaultAromaMeta = 'KPI: ' . data_get($defaultAromaPlan, 'kpi_target', '-')
      . ' • Jangka Waktu: ' . (int) data_get($defaultAromaPlan, 'horizon_hari', 0) . ' hari'
      . ' • Tingkat Keyakinan: ' . $toConfidenceLabel(data_get($defaultAromaPlan, 'confidence', '-'));
    $defaultKetahananMeta = 'KPI: ' . data_get($defaultKetahananPlan, 'kpi_target', '-')
      . ' • Jangka Waktu: ' . (int) data_get($defaultKetahananPlan, 'horizon_hari', 0) . ' hari'
      . ' • Tingkat Keyakinan: ' . $toConfidenceLabel(data_get($defaultKetahananPlan, 'confidence', '-'));
    $kemasanMeta = 'KPI: ' . data_get($kemasanGlobalPlan, 'kpi_target', '-')
      . ' • Jangka Waktu: ' . (int) data_get($kemasanGlobalPlan, 'horizon_hari', 0) . ' hari'
      . ' • Tingkat Keyakinan: ' . $toConfidenceLabel(data_get($kemasanGlobalPlan, 'confidence', '-'));

    $segmentasi = data_get($result ?? [], 'segmentasi_responden', []);
    $segKolom = data_get($segmentasi, 'kolom_pengalaman');
    $segMode = data_get($segmentasi, 'mode_analisis', '-');
    $segTotal = (int) data_get($segmentasi, 'total_responden', 0);
    $segSudah = (int) data_get($segmentasi, 'sudah_pakai', 0);
    $segBelum = (int) data_get($segmentasi, 'belum_pakai.jumlah', 0);
    $segUnknown = (int) data_get($segmentasi, 'pengalaman_tidak_diketahui', 0);
    $segCatatan = data_get($segmentasi, 'catatan_filter');
    $segTopBelum = data_get($segmentasi, 'belum_pakai.top_kata', []);
    $segNonUserInsights = data_get($segmentasi, 'belum_pakai.insights', []);
    $segBarrierTop = data_get($segNonUserInsights, 'barrier_top', []);
    $segNeedTop = data_get($segNonUserInsights, 'need_top', []);
    $segTriggerTop = data_get($segNonUserInsights, 'trigger_top', []);
    $segIntent = data_get($segNonUserInsights, 'intent', []);
    $segAksi = data_get($segNonUserInsights, 'rekomendasi_aksi', []);

    $labelBarrierMap = [
      'harga' => 'Harga awal',
      'belum_tahu_produk' => 'Belum kenal produk',
      'akses_pembelian' => 'Akses pembelian',
      'ragu_kualitas' => 'Keraguan kualitas',
      'sensitivitas' => 'Isu sensitivitas',
    ];
    $labelNeedMap = [
      'aroma_soft' => 'Aroma lebih soft',
      'ketahanan_lama' => 'Ketahanan lebih lama',
      'harga_terjangkau' => 'Harga terjangkau',
      'kemasan_travel' => 'Kemasan travel',
      'jaminan_produk' => 'Jaminan produk',
    ];
    $labelTriggerMap = [
      'tester_sample' => 'Tester / sampel',
      'promo_diskon' => 'Promosi / diskon',
      'rekomendasi_sosial' => 'Rekomendasi sosial',
      'garansi_kepercayaan' => 'Garansi kepercayaan',
    ];

    $formatInsightItems = function ($items, $labelMap = []) {
      if (empty($items))
        return '-';
      return implode(', ', array_map(function ($x) use ($labelMap) {
        $raw = (string) data_get($x, 'label', '-');
        $label = data_get($labelMap, $raw, ucwords(str_replace('_', ' ', $raw)));
        $freq = (int) data_get($x, 'frekuensi', 0);
        return $label . ' (' . $freq . ')';
      }, $items));
    };

    $segBarrierText = $formatInsightItems($segBarrierTop, $labelBarrierMap);
    $segNeedText = $formatInsightItems($segNeedTop, $labelNeedMap);
    $segTriggerText = $formatInsightItems($segTriggerTop, $labelTriggerMap);
    $segIntentLevelRaw = strtolower((string) data_get($segIntent, 'level', 'rendah'));
    $segIntentBadgeClass = $segIntentLevelRaw === 'tinggi' ? 'high' : ($segIntentLevelRaw === 'sedang' ? 'medium' : 'low');
    $segIntentLabel = $segIntentLevelRaw === 'tinggi' ? 'TINGGI' : ($segIntentLevelRaw === 'sedang' ? 'SEDANG' : 'RENDAH');

    $segmentViews = data_get($result ?? [], 'segment_views', []);
    $defaultSegmentView = data_get($segmentasi, 'default_segment_view', 'all');
    $rekomSegmentAwal = data_get($segmentViews, $defaultSegmentView . '.rekomendasi', []);
    $trendAwal = data_get($segmentViews, $defaultSegmentView . '.trend_periode', []);
    $earlyWarningAwal = data_get($segmentViews, $defaultSegmentView . '.early_warning', []);
    $trendMeta = data_get($result ?? [], 'trend_meta', []);
    $trendPeriodCol = data_get($trendMeta, 'period_col');
    $operationalReadiness = data_get($result ?? [], 'operational_readiness', []);
    $opLevel = strtolower((string) data_get($operationalReadiness, 'level', 'not_ready'));
    $opScore = (int) data_get($operationalReadiness, 'score', 0);
    $opChecks = data_get($operationalReadiness, 'checks', []);
    $opWarnings = data_get($operationalReadiness, 'warnings', []);
    $opReadyBiz = (bool) data_get($operationalReadiness, 'ready_for_business_use', false);
    $opReadyAuto = (bool) data_get($operationalReadiness, 'ready_for_auto_actions', false);
    $logoFileCandidates = [
      'logo-luxuex-transparent.png',
      'logo-transparent.png',
      'logo-luxuex.png',
      'logo.png',
    ];
    $brandLogoCandidates = [];
    foreach ($logoFileCandidates as $fileName) {
      if (file_exists(public_path($fileName))) {
        $brandLogoCandidates[] = asset($fileName);
      }
    }
    $brandLogoPrimary = $brandLogoCandidates[0] ?? asset('logo-luxuex-transparent.png');
    $brandLogoFallback = $brandLogoCandidates[1] ?? $brandLogoPrimary;
    $opBadgeClass = $opLevel === 'ready' ? 'high' : ($opLevel === 'limited' ? 'medium' : 'low');
    $opLevelLabel = $opLevel === 'ready' ? 'SIAP' : ($opLevel === 'limited' ? 'TERBATAS' : 'BELUM SIAP');
    $healthCheck = data_get($result ?? [], 'health_check', []);
    $healthIssues = data_get($healthCheck, 'issues', []);
    $alertAspek = data_get($result ?? [], 'alerts.aspek', []);
    $viewError = $error ?? session('error');

    $maxNeg = 0;
    foreach ($prio as $p) {
      $v = (int) data_get($p, 'total_negatif', 0);
      if ($v > $maxNeg)
        $maxNeg = $v;
    }

    $maxCount = 0;
    foreach ($sentAspek as $s) {
      $c = (int) data_get($s, 'total', 0);
      if ($c > $maxCount)
        $maxCount = $c;
    }
  @endphp

  <div class="wrap">

    <section class="hero">
      <div class="goldTop"></div>
      <div class="goldBottom"></div>

      {{-- wave kanan --}}
      <svg class="wave" viewBox="0 0 900 420" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stop-color="rgba(214,181,74,0)" />
            <stop offset="0.5" stop-color="rgba(214,181,74,.55)" />
            <stop offset="1" stop-color="rgba(214,181,74,0)" />
          </linearGradient>
        </defs>
        <path d="M80,250 C220,160 360,320 500,230 C640,140 720,260 860,180" fill="none" stroke="url(#g)"
          stroke-width="2" opacity=".85" />
        <path d="M120,290 C260,200 380,340 520,260 C660,180 740,300 880,220" fill="none" stroke="url(#g)"
          stroke-width="2" opacity=".55" />
        <path d="M60,210 C210,120 350,280 490,190 C630,100 710,220 850,140" fill="none" stroke="url(#g)"
          stroke-width="2" opacity=".40" />
      </svg>

      <div class="heroTop">
        <div class="logoBadge">
          <img id="brandLogoImg" class="loading" src="{{ asset('logo-luxuex-transparent.png') }}" alt="Logo Luxuex"
            onerror="(function(){if(this.dataset.fallback==='1'){this.style.display='none';this.parentElement.querySelector('.logoFallback').style.display='flex';return;}this.dataset.fallback='1';this.classList.add('loading');this.src='{{ $brandLogoFallback }}';}).call(this);"
            onload="this.classList.remove('loading');">
          <div class="logoFallback">L</div>
        </div>
        <div class="brand">
          <div class="name">LUXUEX</div>
          <div class="tag">Luxuex Perfume</div>
        </div>
      </div>

      <div class="heroTitle">Analisis Sentimen Berbasis ABSA</div>
      <div class="heroSub">Masukkan tautan Google Sheets/CSV, kemudian klik Analisis untuk menampilkan hasil pada
        dashboard.</div>

      @if(!empty($viewError))
        <div class="err"><b>Error:</b> {{ $viewError }}</div>
      @endif

      <form method="POST" action="{{ route('absa.analyze') }}" class="heroForm" id="analyzeForm">
        @csrf
        <input class="inp" name="sheet_csv_url"
          placeholder="Contoh: https://docs.google.com/spreadsheets/d/ID/export?format=csv&gid=0"
          value="{{ old('sheet_csv_url') }}" required>
        @if(!empty($opsKeyRequired))
          <input class="inp" type="password" name="dashboard_key" placeholder="Kunci Operasional Dashboard"
            autocomplete="off" required>
        @endif
        <button class="btn" type="submit" id="analyzeSubmitBtn">
          <span class="g">📄</span>
          <span class="btnLabel">Analisis</span>
          <span class="btnSpinner" aria-hidden="true" hidden></span>
        </button>
        <div class="hint">*Pastikan Google Sheet “Anyone with the link” dan URL sudah <b>export?format=csv</b>.</div>
        <div class="loadingEstimateTools">
          <button type="button" class="loadingEstimateReset" id="resetLoadingEstimateBtn">Reset estimasi
            loading</button>
          @if(!empty($result))
            <a href="{{ route('absa.index') }}" class="loadingEstimateReset" id="resetDashboardBtn">Atur ulang dashboard
              (hapus
              tampilan hasil)</a>
          @endif
          <span class="loadingEstimateInfo" id="resetLoadingEstimateInfo" aria-live="polite"></span>
        </div>
      </form>

      <div class="viewToggle">
        <button type="button" id="compactModeBtn" class="toggleBtn" aria-pressed="false">Normal</button>
        <button type="button" id="resetCompactModeBtn" class="toggleBtn secondary">Otomatis</button>
      </div>
    </section>

    <div class="grid">
      <div class="sectionTitle"><span class="dot"></span>Dashboard</div>

      @if(!empty($segmentViews))
        <div class="panel segCtl">
          <div>
            <div class="mini"><b>Filter Segmen</b></div>
            <div class="mini" id="segmentLabel" style="margin-top:4px">Segmen aktif:
              {{ $defaultSegmentView === 'used' ? 'Sudah Menggunakan (Analisis Produk)' : ($defaultSegmentView === 'non_user' ? 'Belum Menggunakan (Calon Pembeli)' : 'Seluruh Responden') }}
            </div>
          </div>
          <div class="segBtns">
            <button type="button" class="segBtn {{ $defaultSegmentView === 'all' ? 'active' : '' }}"
              data-segment="all">Seluruh Responden</button>
            <button type="button" class="segBtn {{ $defaultSegmentView === 'used' ? 'active' : '' }}"
              data-segment="used">Sudah Menggunakan (Analisis Produk)</button>
            <button type="button" class="segBtn {{ $defaultSegmentView === 'non_user' ? 'active' : '' }}"
              data-segment="non_user">Belum Menggunakan (Calon Pembeli)</button>
          </div>
        </div>
      @endif

      @if(!empty($operationalReadiness))
        <div class="panel opsReadiness">
          <div class="opsReadinessHead">
            <h3 style="margin:0">Kesiapan Operasional</h3>
            <div class="opsReadinessScore">Skor: {{ $opScore }}/100</div>
          </div>
          <div class="mini" style="margin-bottom:8px;">Status pemakaian lapangan:</div>
          <div class="opsReadinessTitle">
            <span>Level Kesiapan</span>
            <span class="intentBadge {{ $opBadgeClass }}">{{ $opLevelLabel }}</span>
          </div>
          <div class="mini" style="margin-top:6px;">
            Siap bisnis: <b>{{ $opReadyBiz ? 'YA' : 'BELUM' }}</b> • Otomatisasi aksi:
            <b>{{ $opReadyAuto ? 'YA' : 'BELUM' }}</b>
          </div>

          @if(!empty($opChecks))
            <div class="opsReadinessGrid">
              @foreach($opChecks as $ck)
                @php
                  $checkPassed = (bool) data_get($ck, 'passed', false);
                  $checkBadge = $checkPassed ? 'high' : 'low';
                  $checkLabel = ucfirst(str_replace('_', ' ', (string) data_get($ck, 'key', '-')));
                  $checkNote = (string) data_get($ck, 'note', '-');
                @endphp
                <div class="opsReadinessBox">
                  <div class="opsReadinessTitle">
                    <span>{{ $checkLabel }}</span>
                    <span class="intentBadge {{ $checkBadge }}">{{ $checkPassed ? 'OK' : 'PERLU' }}</span>
                  </div>
                  <div class="mini">{{ $checkNote }}</div>
                </div>
              @endforeach
            </div>
          @endif

          @if(!empty($opWarnings))
            <div class="mini" style="margin-top:10px;color:#f7b955;"><b>Catatan Penting:</b></div>
            <ul class="opsWarnings">
              @foreach($opWarnings as $warn)
                <li>{{ $warn }}</li>
              @endforeach
            </ul>
          @endif
        </div>
      @endif

      @if(!empty($healthCheck) || !empty($alertAspek))
        <div class="panel" id="healthScopedArea" style="grid-column:span 12">
          <h3>Pemeriksaan Kualitas Data & Peringatan Aksi</h3>
          @if(!empty($healthIssues))
            <div class="mini" style="margin-bottom:8px;color:#f7b955;"><b>Catatan Kualitas Data/Model:</b></div>
            <ul class="drillList" style="margin-top:0;margin-bottom:10px;">
              @foreach($healthIssues as $issue)
                <li>{{ $issue }}</li>
              @endforeach
            </ul>
          @else
            <div class="mini" style="margin-bottom:10px;color:#8ee08e;"><b>Data dan model berada pada kondisi memadai
                untuk pemantauan rutin.</b></div>
          @endif

          @if(!empty($alertAspek))
            <div class="tableScrollX">
              <table class="healthAlertTable">
                <thead>
                  <tr>
                    <th>Aspek</th>
                    <th>Level</th>
                    <th>Negatif</th>
                    <th>Rekomendasi Tindak Lanjut</th>
                  </tr>
                </thead>
                <tbody>
                  @foreach($alertAspek as $al)
                    @php
                      $alertAspect = ucwords(strtolower((string) data_get($al, 'aspek', '-')));
                      $alertLevelRaw = strtolower((string) data_get($al, 'level', 'low'));
                      $alertBadgeClass = $alertLevelRaw === 'high' ? 'high' : ($alertLevelRaw === 'medium' ? 'medium' : 'low');
                      $alertLevelText = $alertLevelRaw === 'high' ? 'TINGGI' : ($alertLevelRaw === 'medium' ? 'SEDANG' : 'RENDAH');
                      $alertTextRaw = trim((string) preg_replace('/\s+/', ' ', (string) data_get($al, 'text', '-')));
                      if ($alertTextRaw === '' || $alertTextRaw === '-') {
                        $alertText = '-';
                      } else {
                        $alertText = ucfirst($alertTextRaw);
                        $prefix = strtolower($alertAspect) . ':';
                        if (!str_starts_with(strtolower($alertText), $prefix)) {
                          $alertText = $alertAspect . ': ' . ltrim($alertText, ': ');
                        }
                      }
                    @endphp
                    <tr>
                      <td>{{ $alertAspect }}</td>
                      <td><span class="intentBadge {{ $alertBadgeClass }}">{{ $alertLevelText }}</span></td>
                      <td>{{ number_format((float) data_get($al, 'persen_negatif', 0), 1) }}%</td>
                      <td title="{{ $alertText }}"><span class="quickRecoText">{{ $alertText }}</span></td>
                    </tr>
                  @endforeach
                </tbody>
              </table>
            </div>
          @endif

          <div class="mini" style="margin-top:12px;margin-bottom:6px;"><b>Peringatan Dini (Segmen Aktif)</b></div>
          <div class="tableScrollX">
            <table class="earlyWarnTable">
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Indikator</th>
                  <th>Nilai</th>
                  <th>Catatan</th>
                </tr>
              </thead>
              <tbody id="earlyWarnBody">
                @forelse($earlyWarningAwal as $ew)
                  @php
                    $ewLevelRaw = strtolower((string) data_get($ew, 'level', 'low'));
                    $ewBadgeClass = $ewLevelRaw === 'high' ? 'high' : ($ewLevelRaw === 'medium' ? 'medium' : 'low');
                    $ewLevelText = $ewLevelRaw === 'high' ? 'TINGGI' : ($ewLevelRaw === 'medium' ? 'SEDANG' : 'RENDAH');
                  @endphp
                  <tr>
                    <td><span class="intentBadge {{ $ewBadgeClass }}">{{ $ewLevelText }}</span></td>
                    <td>{{ data_get($ew, 'indikator', '-') }}</td>
                    <td>{{ data_get($ew, 'value', '-') }}</td>
                    <td><span class="quickRecoText">{{ data_get($ew, 'text', '-') }}</span></td>
                  </tr>
                @empty
                  <tr>
                    <td colspan="4" style="color:rgba(255,255,255,.65)">Belum terdapat peringatan dini pada segmen ini.</td>
                  </tr>
                @endforelse
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel hintPanel" id="healthScopedHint" style="grid-column:span 12;display:none;">
          <div class="mini">Pemeriksaan kualitas data dan peringatan aksi hanya ditampilkan untuk segmen Seluruh
            Responden atau Sudah Menggunakan.</div>
        </div>
      @endif

      <div class="panel gold kpi kpiSimple">
        <div class="ico">💬</div>
        <div class="kpiMain">
          <div class="label">Jumlah Komentar</div>
          <div class="value" id="kpiJumlahValue">{{ is_numeric($jumlahKomentar) ? $jumlahKomentar : '—' }}</div>
        </div>
        <div class="spark"></div>
      </div>

      <div class="panel gold kpi kpiDetail">
        <div class="ico">✅</div>
        <div class="kpiMain">
          @if(!empty($operationalReadiness))
            <div class="kpiReadiness">
              <span class="intentBadge {{ $opBadgeClass }}">{{ $opLevelLabel }}</span>
              <span class="kpiReadinessMeta">Kesiapan {{ $opScore }}/100</span>
            </div>
          @endif
          <div class="label">
            @if(data_get($kpi, 'model_trained'))
              F1 Score <small style="font-weight:normal;">(ML)</small>
            @else
              Akurasi <small style="font-weight:normal;">(rule)</small>
            @endif
          </div>
          <div class="value">{{ $akurasiText }}</div>

          @if(data_get($kpi, 'model_trained'))
            <div class="mini mlStats">
              <div class="modelLine"><strong>Model:</strong> {{ data_get($kpi, 'model_used', '-') }}</div>

              <div class="metricRow">
                <span class="metricName">F1 Score (weighted)</span>
                <span class="metricPair"><strong>NB:</strong>
                  {{ is_numeric(data_get($kpi, 'f1_nb')) ? number_format(data_get($kpi, 'f1_nb') * 100, 1) . '%' : '—' }}</span>
                <span class="sep">|</span>
                <span class="metricPair"><strong>SVM:</strong>
                  {{ is_numeric(data_get($kpi, 'f1_svm')) ? number_format(data_get($kpi, 'f1_svm') * 100, 1) . '%' : '—' }}</span>
              </div>

              <div class="metricRow">
                <span class="metricName">Accuracy</span>
                <span class="metricPair"><strong>NB:</strong>
                  {{ is_numeric(data_get($kpi, 'accuracy_nb')) ? number_format(data_get($kpi, 'accuracy_nb') * 100, 1) . '%' : '—' }}</span>
                <span class="sep">|</span>
                <span class="metricPair"><strong>SVM:</strong>
                  {{ is_numeric(data_get($kpi, 'accuracy_svm')) ? number_format(data_get($kpi, 'accuracy_svm') * 100, 1) . '%' : '—' }}</span>
              </div>

              <div class="metricRow">
                <span class="metricName">Precision</span>
                <span class="metricPair"><strong>NB:</strong>
                  {{ is_numeric(data_get($kpi, 'precision_nb')) ? number_format(data_get($kpi, 'precision_nb') * 100, 1) . '%' : '—' }}</span>
                <span class="sep">|</span>
                <span class="metricPair"><strong>SVM:</strong>
                  {{ is_numeric(data_get($kpi, 'precision_svm')) ? number_format(data_get($kpi, 'precision_svm') * 100, 1) . '%' : '—' }}</span>
              </div>

              <div class="metricRow">
                <span class="metricName">Recall</span>
                <span class="metricPair"><strong>NB:</strong>
                  {{ is_numeric(data_get($kpi, 'recall_nb')) ? number_format(data_get($kpi, 'recall_nb') * 100, 1) . '%' : '—' }}</span>
                <span class="sep">|</span>
                <span class="metricPair"><strong>SVM:</strong>
                  {{ is_numeric(data_get($kpi, 'recall_svm')) ? number_format(data_get($kpi, 'recall_svm') * 100, 1) . '%' : '—' }}</span>
              </div>
            </div>
          @else
            <div class="mini mlStats">
              <div class="metricRow">
                <span class="metricName">Test Accuracy</span>
                <span class="metricPair"><strong>NB:</strong>
                  {{ is_numeric(data_get($kpi, 'accuracy_nb')) ? number_format(data_get($kpi, 'accuracy_nb') * 100, 1) . '%' : '—' }}</span>
                <span class="sep">|</span>
                <span class="metricPair"><strong>SVM:</strong>
                  {{ is_numeric(data_get($kpi, 'accuracy_svm')) ? number_format(data_get($kpi, 'accuracy_svm') * 100, 1) . '%' : '—' }}</span>
              </div>
            </div>
          @endif

          @php $reason = data_get($kpi, 'training_reason'); @endphp
          @if($reason)
            <div class="kpiMeta">({{ $reason }})</div>
          @endif
        </div>
        <div class="spark"></div>
      </div>



      <div class="panel gold kpi kpiSimple">
        <div class="ico">😕</div>
        <div class="kpiMain">
          <div class="label">Sentimen Negatif</div>
          <div class="value" id="kpiNegatifValue">{{ $negatifText }}</div>
        </div>
        <div class="spark"></div>
      </div>

      <div class="panel" style="grid-column:span 12" id="trendScopedArea">
        <h3>Tren per Periode</h3>
        <div class="mini segContext" id="panelCtxTrend" style="margin-top:-6px;margin-bottom:8px">Berdasarkan segmen
          aktif.</div>
        <div class="mini" style="margin-bottom:10px">
          Sumber periode:
          @if(!empty($trendPeriodCol))
            <b>{{ $trendPeriodCol }}</b>
          @else
            <span>Tidak terdeteksi (pastikan tersedia kolom tanggal atau stempel waktu).</span>
          @endif
        </div>

        <div class="tableScrollX">
          <table class="trendTable">
            <thead>
              <tr>
                <th style="width:24%">Periode</th>
                <th style="width:20%">Jumlah Data</th>
                <th style="width:20%">Negatif</th>
                <th>Negatif (%)</th>
              </tr>
            </thead>
            <tbody id="trendPeriodeBody">
              @forelse($trendAwal as $tr)
                <tr>
                  <td>{{ data_get($tr, 'periode', '-') }}</td>
                  <td>{{ (int) data_get($tr, 'jumlah_komentar', 0) }}</td>
                  <td>{{ (int) data_get($tr, 'negatif', 0) }}</td>
                  <td>{{ number_format((float) data_get($tr, 'persen_negatif', 0), 1) }}%</td>
                </tr>
              @empty
                <tr>
                  <td colspan="4" style="color:rgba(255,255,255,.65)">Belum tersedia data tren periode pada segmen ini.
                  </td>
                </tr>
              @endforelse
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel" style="grid-column:span 12" id="segmentCompareArea">
        <h3>Perbandingan Segmen</h3>
        <div class="mini" style="margin-top:-6px;margin-bottom:10px">Perbandingan antar segmen untuk indikator
          utama analisis.</div>
        <div class="tableScrollX">
          <table class="segmentCompareTable">
            <thead>
              <tr>
                <th style="width:26%">Segmen</th>
                <th style="width:16%">Jumlah Komentar</th>
                <th style="width:18%">Sentimen Negatif</th>
                <th style="width:16%">Aspek Prioritas</th>
                <th>Status Peringatan</th>
              </tr>
            </thead>
            <tbody id="segmentCompareBody">
              <tr>
                <td colspan="5" style="color:rgba(255,255,255,.65)">Memuat ringkasan perbandingan segmen...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      @if(!empty($segmentasi))
        <div class="panel" id="nonUserOnlySection" style="grid-column:span 12">
          <h3>Analisis Segmen Calon Pembeli (Belum Pernah Pakai)</h3>
          <div class="mini" style="margin-top:2px;margin-bottom:8px">Fokus: hambatan adopsi, kebutuhan utama, dan
            pendorong konversi.</div>
          <div class="mini" style="margin-bottom:10px;line-height:1.5">
            <b>Mode analisis utama:</b>
            {{ $segMode === 'sudah_pakai' ? 'Hanya responden yang sudah menggunakan' : 'Seluruh data (mode cadangan)' }}
            @if(!empty($segKolom))
              <br><b>Kolom deteksi pengalaman:</b> {{ $segKolom }}
            @endif
            @if(!empty($segCatatan))
              <br><span style="color:#f7b955">{{ $segCatatan }}</span>
            @endif
          </div>

          <div class="tableScrollX" style="margin-bottom:10px;">
            <table class="segmentSummaryTable">
              <thead>
                <tr>
                  <th>Total Responden</th>
                  <th>Sudah Pernah Pakai</th>
                  <th>Belum Pernah Pakai</th>
                  <th>Tidak Diketahui</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ $segTotal }}</td>
                  <td>{{ $segSudah }}</td>
                  <td>{{ $segBelum }}</td>
                  <td>{{ $segUnknown }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mini" style="margin-top:2px;margin-bottom:6px"><b>Kata kunci dominan pada segmen calon pembeli</b>
          </div>
          <div class="chips">
            @forelse(array_slice($segTopBelum, 0, 6) as $tk)
              <div class="chip">
                <span>{{ data_get($tk, 'kata', '-') }}</span>
                <b>{{ (int) data_get($tk, 'frekuensi', 0) }}</b>
              </div>
            @empty
              <div class="mini">Belum terdapat kata kunci yang terdeteksi pada segmen ini.</div>
            @endforelse
          </div>

          @if(!empty($segNonUserInsights))
            <div class="mini" style="margin-top:12px;margin-bottom:6px"><b>Ringkasan Wawasan Calon Pembeli</b></div>
            <div class="tableScrollX" style="margin-bottom:10px;">
              <table>
                <thead>
                  <tr>
                    <th style="width:26%">Kategori</th>
                    <th>Temuan Prioritas</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Hambatan Utama</td>
                    <td>{{ $segBarrierText }}</td>
                  </tr>
                  <tr>
                    <td>Kebutuhan Produk</td>
                    <td>{{ $segNeedText }}</td>
                  </tr>
                  <tr>
                    <td>Pendorong Pembelian</td>
                    <td>{{ $segTriggerText }}</td>
                  </tr>
                  <tr>
                    <td>Skor Minat Coba</td>
                    <td>
                      {{ number_format((float) data_get($segIntent, 'score', 0), 1) }} / 100
                      <span class="intentBadge {{ $segIntentBadgeClass }}">{{ $segIntentLabel }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="mini" style="margin-top:4px;margin-bottom:6px"><b>Rekomendasi Aksi Produk & Akuisisi</b></div>
            <ul class="drillList" style="margin-top:0;">
              @forelse($segAksi as $aksi)
                <li>{{ $aksi }}</li>
              @empty
                <li>Lakukan uji coba terbatas, penawaran bundling, dan edukasi manfaat untuk meningkatkan minat mencoba.</li>
              @endforelse
            </ul>
          @endif
        </div>
      @endif

      {{-- ABSA --}}
      <div class="panel absa">
        <h3>Analisis ABSA</h3>

        <div class="absaGrid">
          <div>
            <div class="mini" style="display:flex;justify-content:space-between">
              <span><b style="color:rgba(255,255,255,.86)">Prediksi</b></span>
              <span><b style="color:rgba(255,255,255,.86)">Aktual</b></span>
            </div>

            <div class="cm">
              <div class="axis">Sebenarnya</div>
              <div class="colhdr">Prediksi</div>
              <div class="colhdr">Aktual</div>

              <div class="mat">
                <div class="cell c1">{{ $tp }}</div>
                <div class="cell c2">{{ $fp }}</div>
                <div class="cell c3">{{ $fn }}</div>
                <div class="cell c4">{{ $tn }}</div>
              </div>
            </div>

            <div class="legend">
              <span class="pill"><span class="sw g"></span> Positif Benar (TP)</span>
              <span class="pill"><span class="sw y"></span> Positif Salah (FP)</span>
              <span class="pill"><span class="sw r"></span> Negatif Salah (FN)</span>
              <span class="pill"><span class="sw n"></span> Negatif Benar (TN)</span>
            </div>
          </div>

          <div>
            <div class="mini" style="margin-top:4px;margin-bottom:12px">
              <b style="color:rgba(255,255,255,.86)">Distribusi Sentimen Aspek Utama</b>
            </div>

            <div class="cm">
              <div class="axis">Sentimen</div>
              <div class="colhdr">Positif</div>
              <div class="colhdr">Negatif</div>

              <div class="mat">
                <div class="cell c1">{{ $tp }}</div>
                <div class="cell c2">{{ $fp }}</div>
                <div class="cell c3">{{ $fn }}</div>
                <div class="cell c4">{{ $tn }}</div>
              </div>
            </div>

            <div class="legend">
              <span class="pill"><span class="sw g"></span> Positif</span>
              <span class="pill"><span class="sw y"></span> Netral</span>
              <span class="pill"><span class="sw r"></span> Negatif</span>
            </div>
          </div>

          <div>
            <div class="mini" style="margin-top:4px;margin-bottom:8px">
              <b style="color:rgba(255,255,255,.86)">Kata Kunci Teratas dari Komentar</b>
            </div>

            <div class="chips" id="topKataChips">
              @forelse(array_slice($topKata, 0, 4) as $tk)
                <div class="chip">
                  <span>{{ data_get($tk, 'kata', '-') }}</span>
                  <b>{{ (int) data_get($tk, 'frekuensi', 0) }}</b>
                </div>
              @empty
                <div class="mini">Belum terdapat kata kunci terdeteksi.</div>
              @endforelse
            </div>
          </div>
        </div>
      </div>

      {{-- Sentimen per aspek --}}
      <div class="panel sentim" id="sentimScopedArea">
        <h3>Sentimen per Aspek</h3>
        <div class="mini segContext" id="panelCtxSentim" style="margin-top:-6px;margin-bottom:10px">Berdasarkan segmen
          aktif.</div>

        <div class="donutWrap">
          <div class="donut" id="sentimDonut" style="--pct: {{ $donutPct }}%;">
            <div class="pctTxt" id="sentimDonutText">{{ $donutPct }}%</div>
          </div>

          <div class="breakdown" id="sentimBreakdown">
            @foreach(array_slice($sentAspek, 0, 3) as $s)
              @php
                $persenNeg = (float) data_get($s, 'persen_negatif', 0);
                $total = (int) data_get($s, 'total', 0);
                // fallback ke positif jika negatif nol
                if ($persenNeg <= 0 && $total > 0) {
                  $persenNeg = round((data_get($s, 'positif', 0) / $total) * 100, 1);
                }
              @endphp
              <div class="brow">
                <div class="k">{{ data_get($s, 'aspek', '-') }}</div>
                <div class="v">{{ round($persenNeg, 1) }}%</div>
              </div>
            @endforeach
          </div>
        </div>

        <div class="miniBars" id="sentimBars">
          @foreach(array_slice($sentAspek, 0, 3) as $s)
            @php
              $nm = data_get($s, 'aspek', '-');
              $ct = (int) data_get($s, 'total', 0);
              $w = $maxCount > 0 ? max(3, round(($ct / $maxCount) * 100)) : 0;
            @endphp
            <div class="barRow">
              <div class="name">{{ $nm }}</div>
              <div class="bar">
                <div class="fill" style="width:{{ $w }}%"></div>
              </div>
              <div class="p">{{ $ct }}</div>
            </div>
          @endforeach
        </div>
      </div>
      <div class="panel hintPanel" id="sentimScopedHint" style="grid-column:span 12;display:none;">
        <div class="mini">Sentimen per Aspek hanya ditampilkan untuk segmen Seluruh Responden atau Sudah Menggunakan.
        </div>
      </div>

      {{-- Top isu --}}
      <div class="panel isu" id="isuScopedArea">
        <h3>Isu Teratas per Aspek</h3>
        <div class="mini segContext" id="panelCtxIsu" style="margin-top:-6px;margin-bottom:10px">Berdasarkan segmen
          aktif.</div>
        <div class="tableScrollX">
          <table class="topIsuTable">
            <thead>
              <tr>
                <th style="width:26%">Aspek</th>
                <th>Isu Dominan</th>
                <th style="width:18%">Frekuensi</th>
              </tr>
            </thead>
            <tbody id="topIsuBody">
              @forelse($topIsu as $row)
                <tr>
                  <td>{{ data_get($row, 'aspek', '-') }}</td>
                  <td>{{ data_get($row, 'isu', '-') }}</td>
                  <td>{{ (int) data_get($row, 'frekuensi', 0) }}</td>
                </tr>
              @empty
                <tr>
                  <td colspan="3" style="color:rgba(255,255,255,.65)">Belum tersedia data. Silakan jalankan analisis
                    terlebih dahulu.</td>
                </tr>
              @endforelse
            </tbody>
          </table>
        </div>
      </div>
      <div class="panel hintPanel" id="isuScopedHint" style="grid-column:span 12;display:none;">
        <div class="mini">Isu Teratas per Aspek hanya ditampilkan untuk segmen Seluruh Responden atau Sudah Menggunakan.
        </div>
      </div>

      <div class="panel drill" id="drillScopedArea">
        <h3>Rincian Ulasan per Aspek</h3>
        <div class="mini" style="margin-top:-2px;margin-bottom:10px">Pilih aspek untuk menampilkan contoh komentar
          positif dan negatif pada segmen aktif.</div>
        <div class="segBtns" style="margin-bottom:10px;">
          <button type="button" class="segBtn active" data-aspek="aroma">Aroma</button>
          <button type="button" class="segBtn" data-aspek="kemasan">Kemasan</button>
          <button type="button" class="segBtn" data-aspek="ketahanan">Ketahanan</button>
        </div>

        <div class="drillGrid">
          <div class="drillBox">
            <h4>Komentar Positif <span class="drillCount" id="drillPositifCount">(0)</span></h4>
            <ul class="drillList" id="drillPositifList">
              <li>Belum tersedia data.</li>
            </ul>
          </div>
          <div class="drillBox">
            <h4>Komentar Negatif <span class="drillCount" id="drillNegatifCount">(0)</span></h4>
            <ul class="drillList" id="drillNegatifList">
              <li>Belum tersedia data.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="panel hintPanel" id="drillScopedHint" style="grid-column:span 12;display:none;">
        <div class="mini">Rincian komentar per aspek hanya ditampilkan untuk segmen Seluruh Responden atau Sudah
          Menggunakan.</div>
      </div>

      {{-- Rekomendasi --}}
      <div class="panel rekom">
        <div class="rekomHead">
          <h3 style="margin:0">Rekomendasi Strategis</h3>
          <div class="rekomActions">
            <button type="button" class="miniActionBtn" id="exportManagerPdfBtn">Ekspor PDF Detail (Pemilik)</button>
          </div>
        </div>
        <div class="mini segContext" id="panelCtxRekom" style="margin-top:-6px;margin-bottom:10px">Berdasarkan segmen
          aktif.</div>

        @if(!empty($variants))
          <div id="variantScopedArea">
            <div class="mini" style="margin-bottom:6px"><b>Pilih Varian Parfum</b></div>
            <select id="variantSelect" class="inp" style="width:100%;padding:10px 12px;border-radius:12px;">
              @foreach($variants as $v)
                <option value="{{ $v }}">{{ $v }}</option>
              @endforeach
            </select>
            <div class="mini" id="variantCommentInfo" style="margin-top:6px">Jumlah komentar varian terpilih: -</div>
            <div class="variantSyncHint" id="variantSyncHint">Sinkronisasi segmen sedang dimuat...</div>

            @if(!empty($variantRankings))
              <div class="mini" style="margin-top:10px;margin-bottom:6px"><b>8 Varian Teratas (berdasarkan skor
                  kualitas)</b>
              </div>
              <div class="tableScrollX variantRankScroll" style="margin-bottom:8px;">
                <table class="variantRankTable">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Varian</th>
                      <th>Skor</th>
                      <th>Negatif</th>
                      <th>Komentar</th>
                      <th>Sinkron</th>
                      <th>Isu Dominan</th>
                    </tr>
                  </thead>
                  <tbody id="variantRankBody">
                    @foreach($variantRankings as $vr)
                      <tr>
                        <td>{{ data_get($vr, 'peringkat', '-') }}</td>
                        <td>{{ data_get($vr, 'varian', '-') }}</td>
                        <td>{{ number_format((float) data_get($vr, 'skor_kualitas', 0), 1) }}</td>
                        <td>{{ number_format((float) data_get($vr, 'persen_negatif', 0), 1) }}%</td>
                        <td>{{ (int) data_get($vr, 'total_komentar', 0) }}</td>
                        <td><span class="alignBadge partial">Sebagian</span></td>
                        @php $isuVarian = (string) data_get($vr, 'isu_dominan', '-'); @endphp
                        <td><span class="variantIsuText" title="{{ $isuVarian }}">{{ $isuVarian }}</span></td>
                      </tr>
                    @endforeach
                  </tbody>
                </table>
              </div>
            @endif

            <div class="rekomItem">
              <div class="ricon">🌸</div>
              <div>
                <p class="ttl">Rekomendasi Aroma (per varian)</p>
                <p class="txt" id="recoAromaText">{{ $defaultAromaReco }}</p>
                <p class="mini" id="recoAromaMeta" style="margin-top:4px">{{ $defaultAromaMeta }}</p>
              </div>
            </div>

            <div class="rekomItem">
              <div class="ricon">⏱️</div>
              <div>
                <p class="ttl">Rekomendasi Ketahanan (per varian)</p>
                <p class="txt" id="recoKetahananText">{{ $defaultKetahananReco }}</p>
                <p class="mini" id="recoKetahananMeta" style="margin-top:4px">{{ $defaultKetahananMeta }}</p>
              </div>
            </div>

            <div class="rekomItem">
              <div class="ricon">📦</div>
              <div>
                <p class="ttl">Rekomendasi Kemasan (umum)</p>
                <p class="txt">{{ $kemasanGlobalReco }}</p>
                <p class="mini" style="margin-top:4px">{{ $kemasanMeta }}</p>
              </div>
            </div>
          </div>
          <div id="variantScopedHint" class="mini" style="margin-top:8px;display:none;">Konten varian hanya ditampilkan
            untuk segmen Seluruh Responden atau Sudah Menggunakan.</div>
        @else
          @forelse($rekom as $r)
            <div class="rekomItem">
              <div class="ricon">★</div>
              <div>
                <p class="ttl">{{ data_get($r, 'aspek', '-') }}</p>
                <p class="txt">{{ data_get($r, 'text', '-') }}</p>
                <p class="mini" style="margin-top:4px">
                  KPI: {{ data_get($r, 'kpi_target', '-') }} • Jangka Waktu: {{ (int) data_get($r, 'horizon_hari', 0) }}
                  hari • Tingkat Keyakinan: {{ $toConfidenceLabel(data_get($r, 'confidence', '-')) }}
                </p>
              </div>
            </div>
          @empty
            <div class="mini" style="margin-top:8px">Belum tersedia rekomendasi. Silakan jalankan analisis terlebih dahulu.
            </div>
          @endforelse
        @endif

        <div class="mini" style="margin-top:10px;margin-bottom:6px"><b>Rekomendasi Strategis (Segmen Aktif)</b></div>
        <div id="segmentRekomList">
          @forelse($rekomSegmentAwal as $r)
            <div class="rekomItem">
              <div class="ricon">★</div>
              <div>
                <p class="ttl">{{ data_get($r, 'aspek', '-') }}</p>
                <p class="txt">{{ data_get($r, 'text', '-') }}</p>
                <p class="mini" style="margin-top:4px">
                  KPI: {{ data_get($r, 'kpi_target', '-') }} • Jangka Waktu: {{ (int) data_get($r, 'horizon_hari', 0) }}
                  hari • Tingkat Keyakinan: {{ $toConfidenceLabel(data_get($r, 'confidence', '-')) }}
                </p>
              </div>
            </div>
          @empty
            <div class="mini" style="margin-top:8px">Belum tersedia rekomendasi untuk segmen ini.</div>
          @endforelse
        </div>
      </div>

      {{-- Prioritas --}}
      <div class="panel prio" id="prioScopedArea">
        <h3>Prioritas Perbaikan</h3>
        <div class="mini segContext" id="panelCtxPrio" style="margin-top:-6px;margin-bottom:10px">Berdasarkan segmen
          aktif.</div>
        <div class="mini" style="margin-top:-6px;margin-bottom:10px">Jumlah Komentar Negatif</div>

        <div id="prioritasList">
          @forelse($prio as $p)
            @php
              $nm = data_get($p, 'aspek', '-');
              $val = (int) data_get($p, 'total_negatif', 0);
              $w = ($maxNeg > 0) ? max(3, round(($val / $maxNeg) * 100)) : 0;
            @endphp
            <div class="prioRow">
              <div class="nm">{{ $nm }}</div>
              <div class="prioBar">
                <div class="prioFill" style="width:{{ $w }}%"></div>
              </div>
              <div class="prioVal">{{ $val }}</div>
            </div>
          @empty
            <div class="mini">Belum tersedia prioritas. Silakan jalankan analisis terlebih dahulu.</div>
          @endforelse
        </div>
      </div>
      <div class="panel hintPanel" id="prioScopedHint" style="grid-column:span 12;display:none;">
        <div class="mini">Prioritas Perbaikan hanya ditampilkan untuk segmen Seluruh Responden atau Sudah Menggunakan.
        </div>
      </div>

    </div>
  </div>

  <div class="submitLoadingOverlay" id="submitLoadingOverlay" aria-hidden="true">
    <div class="submitLoadingCard" role="status" aria-live="polite" aria-atomic="true">
      <div class="submitLoadingTitle" id="submitLoadingTitle">Memproses analisis…</div>
      <div class="submitLoadingSub" id="submitLoadingSub">Sedang menyiapkan hasil dashboard. Mohon tunggu sebentar.
      </div>
      <div class="submitLoadingStepProgress" aria-hidden="true">
        <div class="submitLoadingStepFill" id="submitLoadingStepFill"></div>
      </div>
      <div class="submitLoadingStepMeta" id="submitLoadingStepMeta">Tahap 0/4</div>
      <div class="submitSkeletonLine"></div>
      <div class="submitSkeletonLine w80"></div>
      <div class="submitSkeletonLine w62"></div>
    </div>
  </div>

  <button type="button" class="backTopBtn" id="backTopBtn" aria-label="Kembali ke atas"
    title="Kembali ke atas">↑</button>

</body>

<script>
  (function () {
    const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

    const estimateCornerBackground = (data, w, h) => {
      const points = [
        [0, 0],
        [w - 1, 0],
        [0, h - 1],
        [w - 1, h - 1],
        [Math.floor(w * 0.08), Math.floor(h * 0.08)],
        [Math.floor(w * 0.92), Math.floor(h * 0.08)],
        [Math.floor(w * 0.08), Math.floor(h * 0.92)],
        [Math.floor(w * 0.92), Math.floor(h * 0.92)],
      ];

      let rSum = 0;
      let gSum = 0;
      let bSum = 0;
      let count = 0;

      for (const [xRaw, yRaw] of points) {
        const x = clamp(xRaw, 0, w - 1);
        const y = clamp(yRaw, 0, h - 1);
        const idx = ((y * w) + x) * 4;
        const a = data[idx + 3];
        if (a <= 5) continue;
        rSum += data[idx];
        gSum += data[idx + 1];
        bSum += data[idx + 2];
        count += 1;
      }

      if (!count) return null;
      return {
        r: Math.round(rSum / count),
        g: Math.round(gSum / count),
        b: Math.round(bSum / count),
      };
    };

    const hasExistingTransparency = (data) => {
      for (let i = 3; i < data.length; i += 4) {
        if (data[i] < 250) return true;
      }
      return false;
    };

    const stripSolidBackground = (ctx, w, h) => {
      const imgData = ctx.getImageData(0, 0, w, h);
      const data = imgData.data;
      if (hasExistingTransparency(data)) return false;

      const bg = estimateCornerBackground(data, w, h);
      if (!bg) return false;

      const bgLuma = (0.299 * bg.r) + (0.587 * bg.g) + (0.114 * bg.b);
      const tol = bgLuma < 90 ? 52 : (bgLuma > 190 ? 34 : 40);
      const feather = 18;
      let changed = false;

      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const a = data[i + 3];
        if (a === 0) continue;

        const diff = Math.max(
          Math.abs(r - bg.r),
          Math.abs(g - bg.g),
          Math.abs(b - bg.b)
        );

        if (diff <= tol) {
          data[i + 3] = 0;
          changed = true;
          continue;
        }

        if (diff <= tol + feather) {
          const keepRatio = (diff - tol) / feather;
          const nextAlpha = Math.round(a * keepRatio);
          if (nextAlpha < a) {
            data[i + 3] = nextAlpha;
            changed = true;
          }
        }
      }

      if (changed) {
        ctx.putImageData(imgData, 0, 0);
      }
      return changed;
    };

    const processLogoCanvas = (ctx, w, h) => {
      if (!ctx || !w || !h) return false;
      return stripSolidBackground(ctx, w, h);
    };

    const transparentizeLogoElement = (imgEl) => {
      if (!imgEl || imgEl.dataset.bgProcessed === '1') return;

      try {
        const w = imgEl.naturalWidth || imgEl.width;
        const h = imgEl.naturalHeight || imgEl.height;
        if (!w || !h) return;

        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.drawImage(imgEl, 0, 0, w, h);
        const changed = processLogoCanvas(ctx, w, h);
        if (changed) {
          imgEl.src = canvas.toDataURL('image/png');
        }
        imgEl.dataset.bgProcessed = '1';
      } catch (_) {
        imgEl.dataset.bgProcessed = '1';
      }
    };

    window.__absaTransparentizeLogo = transparentizeLogoElement;
    window.__absaProcessLogoCanvas = processLogoCanvas;

    const logoImg = document.getElementById('brandLogoImg');
    if (!logoImg) return;
    if (logoImg.complete) {
      transparentizeLogoElement(logoImg);
    } else {
      logoImg.addEventListener('load', () => transparentizeLogoElement(logoImg), { once: true });
    }
  })();
</script>

@if(!empty($result))
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>
  <script>
    (function () {
      const segmentViews = @json($segmentViews);
      const defaultSegment = @json($defaultSegmentView);
      const operationalReadiness = @json($operationalReadiness);
      const variantRankingsData = @json($variantRankings);
      const brandName = 'LUXUEX Perfume';
      const brandLogoCandidates = @json($brandLogoCandidates);

      const jumlahEl = document.getElementById('kpiJumlahValue');
      const negatifEl = document.getElementById('kpiNegatifValue');
      const topIsuBody = document.getElementById('topIsuBody');
      const topKataChips = document.getElementById('topKataChips');
      const labelEl = document.getElementById('segmentLabel');
      const sentimDonut = document.getElementById('sentimDonut');
      const sentimDonutText = document.getElementById('sentimDonutText');
      const sentimBreakdown = document.getElementById('sentimBreakdown');
      const sentimBars = document.getElementById('sentimBars');
      const panelCtxSentim = document.getElementById('panelCtxSentim');
      const panelCtxIsu = document.getElementById('panelCtxIsu');
      const panelCtxRekom = document.getElementById('panelCtxRekom');
      const panelCtxPrio = document.getElementById('panelCtxPrio');
      const panelCtxTrend = document.getElementById('panelCtxTrend');
      const trendPeriodeBody = document.getElementById('trendPeriodeBody');
      const earlyWarnBody = document.getElementById('earlyWarnBody');
      const segmentCompareBody = document.getElementById('segmentCompareBody');
      const prioritasList = document.getElementById('prioritasList');
      const variantScopedArea = document.getElementById('variantScopedArea');
      const variantScopedHint = document.getElementById('variantScopedHint');
      const healthScopedArea = document.getElementById('healthScopedArea');
      const healthScopedHint = document.getElementById('healthScopedHint');
      const drillScopedArea = document.getElementById('drillScopedArea');
      const drillScopedHint = document.getElementById('drillScopedHint');
      const sentimScopedArea = document.getElementById('sentimScopedArea');
      const sentimScopedHint = document.getElementById('sentimScopedHint');
      const isuScopedArea = document.getElementById('isuScopedArea');
      const isuScopedHint = document.getElementById('isuScopedHint');
      const prioScopedArea = document.getElementById('prioScopedArea');
      const prioScopedHint = document.getElementById('prioScopedHint');
      const nonUserOnlySection = document.getElementById('nonUserOnlySection');
      const segmentRekomList = document.getElementById('segmentRekomList');
      const exportManagerPdfBtn = document.getElementById('exportManagerPdfBtn');
      const variantRankBody = document.getElementById('variantRankBody');
      const variantSyncHint = document.getElementById('variantSyncHint');
      const posList = document.getElementById('drillPositifList');
      const negList = document.getElementById('drillNegatifList');
      const posCountEl = document.getElementById('drillPositifCount');
      const negCountEl = document.getElementById('drillNegatifCount');
      const segButtons = Array.from(document.querySelectorAll('.segBtn[data-segment]'));
      const aspekButtons = Array.from(document.querySelectorAll('.segBtn[data-aspek]'));
      const tableScrollAreas = Array.from(document.querySelectorAll('.tableScrollX'));

      if (!segmentViews || Object.keys(segmentViews).length === 0) return;

      let activeSegment = segmentViews[defaultSegment] ? defaultSegment : 'all';
      let activeAspek = 'aroma';
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const hasGsap = !prefersReducedMotion && typeof window.gsap !== 'undefined';
      const canAnimate = !prefersReducedMotion && typeof window.requestAnimationFrame === 'function';
      const counterRafMap = new WeakMap();
      const counterStateMap = new WeakMap();
      let hasPlayedEntrance = false;

      function normalizeText(value, fallback = '-') {
        const raw = String(value ?? '').replace(/\s+/g, ' ').trim();
        return raw ? raw : fallback;
      }

      function escapeHtml(value) {
        return String(value ?? '')
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      }

      function safeHtml(value, fallback = '-') {
        return escapeHtml(normalizeText(value, fallback));
      }

      function formatAnimatedNumber(value, decimals = 0, suffix = '') {
        const num = Number(value || 0);
        if (!Number.isFinite(num)) return `0${suffix}`;
        const txt = decimals > 0 ? num.toFixed(decimals) : String(Math.round(num));
        return `${txt}${suffix}`;
      }

      function animateNumber(el, toValue, options = {}) {
        if (!el) return;

        const target = Number(toValue);
        if (!Number.isFinite(target)) {
          el.textContent = options.fallback || '—';
          return;
        }

        const decimals = Number.isInteger(options.decimals) ? options.decimals : 0;
        const suffix = options.suffix || '';
        const stored = Number(el.dataset.animValue);
        const start = Number.isFinite(stored) ? stored : 0;
        const duration = Number(options.duration || 650);

        if (hasGsap) {
          const state = counterStateMap.get(el) || { value: start };
          state.value = Number.isFinite(state.value) ? state.value : start;
          counterStateMap.set(el, state);

          window.gsap.killTweensOf(state);
          window.gsap.to(state, {
            value: target,
            duration: Math.max(0.18, duration / 1000),
            ease: 'power2.out',
            overwrite: 'auto',
            onUpdate: () => {
              el.textContent = formatAnimatedNumber(state.value, decimals, suffix);
            },
            onComplete: () => {
              el.dataset.animValue = String(target);
            }
          });
          return;
        }

        const stopPrev = counterRafMap.get(el);
        if (stopPrev) {
          window.cancelAnimationFrame(stopPrev);
        }

        if (!canAnimate) {
          el.textContent = formatAnimatedNumber(target, decimals, suffix);
          el.dataset.animValue = String(target);
          return;
        }

        const startTs = performance.now();
        const easeOut = (t) => 1 - Math.pow(1 - t, 3);

        const tick = (now) => {
          const progress = Math.min(1, (now - startTs) / duration);
          const eased = easeOut(progress);
          const value = start + (target - start) * eased;
          el.textContent = formatAnimatedNumber(value, decimals, suffix);

          if (progress < 1) {
            const nextId = window.requestAnimationFrame(tick);
            counterRafMap.set(el, nextId);
            return;
          }

          el.dataset.animValue = String(target);
          counterRafMap.delete(el);
        };

        const firstId = window.requestAnimationFrame(tick);
        counterRafMap.set(el, firstId);
      }

      function animateContentSwap(nodes) {
        if (hasGsap) {
          nodes.filter(Boolean).forEach((node, idx) => {
            if (node.offsetParent === null) return;
            window.gsap.killTweensOf(node);
            window.gsap.fromTo(
              node,
              { autoAlpha: 0.9, y: 3 },
              {
                autoAlpha: 1,
                y: 0,
                duration: 0.2,
                delay: idx * 0.012,
                ease: 'power2.out',
                overwrite: 'auto'
              }
            );
          });
          return;
        }

        if (!canAnimate) return;

        nodes.filter(Boolean).forEach((node, idx) => {
          if (typeof node.animate !== 'function' || node.offsetParent === null) return;
          node.animate(
            [
              { opacity: 0.9, transform: 'translateY(3px)' },
              { opacity: 1, transform: 'translateY(0)' }
            ],
            {
              duration: 170,
              delay: idx * 8,
              easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
              fill: 'both'
            }
          );
        });
      }

      function animateDashboardEntrance() {
        if (hasPlayedEntrance) return;
        const panels = Array.from(document.querySelectorAll('.grid .panel'));
        if (!panels.length) return;

        if (hasGsap) {
          window.gsap.set(panels, { autoAlpha: 0, y: 8 });
          window.gsap.to(panels, {
            autoAlpha: 1,
            y: 0,
            duration: 0.32,
            stagger: 0.022,
            ease: 'power2.out',
            clearProps: 'opacity,transform'
          });
          hasPlayedEntrance = true;
          return;
        }

        if (!canAnimate) return;

        panels.forEach((panel, idx) => {
          if (typeof panel.animate !== 'function') return;
          panel.animate(
            [
              { opacity: 0, transform: 'translateY(8px)' },
              { opacity: 1, transform: 'translateY(0)' }
            ],
            {
              duration: 280,
              delay: idx * 14,
              easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
              fill: 'both'
            }
          );
        });

        hasPlayedEntrance = true;
      }

      function syncTableScrollHint(container) {
        if (!container) return;
        const maxScroll = Math.max(0, container.scrollWidth - container.clientWidth);
        const current = Math.max(0, container.scrollLeft || 0);
        const canScroll = maxScroll > 8;
        container.classList.toggle('can-scroll', canScroll);
        container.classList.toggle('show-left', canScroll && current > 6);
        container.classList.toggle('show-right', canScroll && current < (maxScroll - 6));
      }

      function syncAllTableScrollHints() {
        tableScrollAreas.forEach(syncTableScrollHint);
      }

      function pct(n) {
        const v = Number(n || 0);
        return `${(v * 100).toFixed(1)}%`;
      }

      function segmentLabel(segmentKey) {
        if (segmentKey === 'used') return 'Sudah Menggunakan (Analisis Produk)';
        if (segmentKey === 'non_user') return 'Belum Menggunakan (Calon Pembeli)';
        return 'Seluruh Responden';
      }

      function renderPanelContext(segmentKey) {
        const txt = `Berdasarkan segmen: ${segmentLabel(segmentKey)}.`;
        const ctxEls = [panelCtxTrend, panelCtxSentim, panelCtxIsu, panelCtxRekom, panelCtxPrio].filter(Boolean);
        ctxEls.forEach((el) => {
          el.textContent = txt;
          el.classList.remove('all', 'used', 'non_user');
          el.classList.add(segmentKey);
        });
      }

      function buildWeeklyRangeLabel() {
        const now = new Date();
        const end = new Date(now);
        end.setDate(end.getDate() + 6);
        const fmt = (d) => {
          const y = d.getFullYear();
          const m = String(d.getMonth() + 1).padStart(2, '0');
          const day = String(d.getDate()).padStart(2, '0');
          return `${y}-${m}-${day}`;
        };
        return `${fmt(now)} s/d ${fmt(end)}`;
      }

      function loadImageAsDataUrl(src) {
        return new Promise((resolve) => {
          if (!src) {
            resolve(null);
            return;
          }
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = () => {
            try {
              const canvas = document.createElement('canvas');
              canvas.width = img.naturalWidth || img.width;
              canvas.height = img.naturalHeight || img.height;
              const ctx = canvas.getContext('2d');
              if (!ctx) {
                resolve(null);
                return;
              }
              ctx.drawImage(img, 0, 0);

              // Fallback transparansi: buang background solid (hitam/putih) jika tidak ada alpha.
              if (typeof window.__absaProcessLogoCanvas === 'function') {
                try {
                  window.__absaProcessLogoCanvas(ctx, canvas.width, canvas.height);
                } catch (_) {
                }
              }

              resolve(canvas.toDataURL('image/png'));
            } catch (_) {
              resolve(null);
            }
          };
          img.onerror = () => resolve(null);
          img.src = src;
        });
      }

      async function resolveBrandLogoDataUrl() {
        for (const candidate of brandLogoCandidates) {
          const dataUrl = await loadImageAsDataUrl(candidate);
          if (dataUrl) return dataUrl;
        }
        return null;
      }

      function drawLogo(doc, dataUrl, x, y, w, h) {
        if (!dataUrl) return;
        try {
          doc.addImage(dataUrl, 'PNG', x, y, w, h, undefined, 'FAST');
        } catch (_) {
        }
      }

      function collectWeeklyRecommendationPayload() {
        const periodLabel = buildWeeklyRangeLabel();
        const readinessLevel = String(operationalReadiness?.level || '-').toUpperCase();
        const readinessScore = Number(operationalReadiness?.score || 0);
        const readinessWarnings = Array.isArray(operationalReadiness?.warnings)
          ? operationalReadiness.warnings
          : [];
        const safeText = (value, fallback = 'Belum ada data') => {
          const txt = String(value ?? '').trim();
          return txt ? txt : fallback;
        };
        const toPct = (value) => {
          const n = Number(value);
          if (!Number.isFinite(n)) return '0.0';
          return n <= 1 ? (n * 100).toFixed(1) : n.toFixed(1);
        };
        const toConfidenceLabel = (value) => {
          const key = String(value || '').trim().toLowerCase();
          if (key === 'high') return 'Tinggi';
          if (key === 'medium') return 'Sedang';
          if (key === 'low') return 'Rendah';
          return key ? key.charAt(0).toUpperCase() + key.slice(1) : '-';
        };

        const segmentRows = [];
        ['all', 'used', 'non_user'].forEach((key) => {
          const view = segmentViews[key] || {};
          const recs = Array.isArray(view.rekomendasi) ? view.rekomendasi : [];
          const segmentName = segmentLabel(key);

          if (!recs.length) {
            segmentRows.push({
              segmentName,
              aspek: 'Belum diisi',
              text: 'Belum tersedia rekomendasi aksi untuk segmen ini.',
              negPct: toPct(view.persen_negatif || 0),
              total: Number(view.jumlah_komentar || 0),
            });
            return;
          }

          recs.slice(0, 3).forEach((rec) => {
            segmentRows.push({
              segmentName,
              aspek: safeText(rec.aspek, 'Belum diisi'),
              text: safeText(rec.text, 'Belum ada rekomendasi aksi'),
              negPct: toPct(view.persen_negatif || 0),
              total: Number(view.jumlah_komentar || 0),
            });
          });
        });

        const variantRows = Array.isArray(variantRankingsData) ? variantRankingsData.slice(0, 8).map((row) => ({
          varian: safeText(row.varian, 'Varian belum diisi'),
          isu: safeText(row.isu_dominan, 'Belum ada isu dominan'),
          confidence: toConfidenceLabel(row.confidence_level),
          score: Number(row.skor_kualitas || 0).toFixed(1),
          sample: Number(row.total_komentar || 0),
          sampleSufficient: Boolean(row.sample_sufficient),
        })) : [];

        return {
          periodLabel,
          readinessLevel,
          readinessScore,
          readinessWarnings,
          segmentRows,
          variantRows,
        };
      }

      async function exportManagerialPdf() {
        const jsPdfLib = window.jspdf && window.jspdf.jsPDF;
        if (!jsPdfLib) {
          window.alert('Fitur PDF belum siap di browser ini. Coba refresh halaman atau ganti browser.');
          return;
        }

        const payload = collectWeeklyRecommendationPayload();
        const logoDataUrl = await resolveBrandLogoDataUrl();
        const doc = new jsPdfLib({ unit: 'pt', format: 'a4' });
        const margin = 34;
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const maxWidth = pageWidth - (margin * 2);
        const contentBottom = pageHeight - margin - 28;
        let y = margin;

        const now = new Date();
        const ts = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

        const readinessLevelLower = String(payload.readinessLevel || '').toLowerCase();
        const readinessColor = readinessLevelLower === 'ready'
          ? [67, 160, 71]
          : (readinessLevelLower === 'limited' ? [229, 169, 52] : [198, 75, 75]);

        const drawFooterWatermark = (pageNo, totalPages) => {
          if (logoDataUrl) {
            drawLogo(doc, logoDataUrl, margin, pageHeight - 30, 14, 14);
          }
          doc.setFont('helvetica', 'normal');
          doc.setFontSize(8);
          doc.setTextColor(152, 152, 152);
          const wmOffset = logoDataUrl ? 18 : 0;
          doc.text(`${brandName} • ${ts}`, margin + wmOffset, pageHeight - 16);
          doc.text(`Halaman ${pageNo}/${totalPages}`, pageWidth - margin, pageHeight - 16, { align: 'right' });
        };

        const ensureSpace = (height, afterPageAdd = null) => {
          if (y + height > contentBottom) {
            doc.addPage();
            y = margin;
            if (typeof afterPageAdd === 'function') afterPageAdd();
          }
        };

        const splitClamped = (text, width, maxLines = 0) => {
          const lines = doc.splitTextToSize(String(text ?? '-'), width);
          if (maxLines > 0 && lines.length > maxLines) {
            const clipped = lines.slice(0, maxLines);
            const last = String(clipped[maxLines - 1] || '').replace(/[\s.]+$/, '');
            clipped[maxLines - 1] = `${last}...`;
            return clipped;
          }
          return lines.length ? lines : ['-'];
        };

        const writeBlock = (text, opts = {}) => {
          const size = Number(opts.size || 11);
          const weight = opts.bold ? 'bold' : 'normal';
          const gap = Number(opts.gap || 4);
          doc.setFont('helvetica', weight);
          doc.setFontSize(size);
          const lines = splitClamped(String(text || '-'), maxWidth);
          lines.forEach((line) => {
            ensureSpace(size + 4);
            doc.setTextColor(26, 26, 26);
            doc.text(line, margin, y);
            y += size + 4;
          });
          y += gap;
        };

        const drawCover = () => {
          const boxH = 118;
          doc.setFillColor(18, 24, 36);
          doc.roundedRect(margin, y, maxWidth, boxH, 12, 12, 'F');
          doc.setFillColor(readinessColor[0], readinessColor[1], readinessColor[2]);
          doc.roundedRect(margin + 12, y + 14, 138, 24, 10, 10, 'F');

          if (logoDataUrl) {
            drawLogo(doc, logoDataUrl, pageWidth - margin - 66, y + 18, 54, 54);
          }

          doc.setTextColor(255, 255, 255);
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(13);
          doc.text(`STATUS ${String(payload.readinessLevel || '-').toUpperCase()}`, margin + 20, y + 31);

          doc.setFont('helvetica', 'bold');
          doc.setFontSize(20);
          doc.text('Ringkasan Eksekutif ABSA', margin + 12, y + 63);

          doc.setFont('helvetica', 'normal');
          doc.setFontSize(10);
          doc.text(`Periode aksi: ${payload.periodLabel}`, margin + 12, y + 83);
          doc.text(`Skor kesiapan: ${payload.readinessScore}/100`, margin + 12, y + 98);
          doc.text(`Siap bisnis: ${Boolean(operationalReadiness?.ready_for_business_use)} | Siap otomatis: ${Boolean(operationalReadiness?.ready_for_auto_actions)}`, margin + 12, y + 112);

          y += boxH + 16;
        };

        const drawSectionTitle = (text, opts = {}) => {
          const topGap = Number(opts.topGap || 0);
          if (topGap > 0) {
            ensureSpace(topGap + 26);
            y += topGap;
          } else {
            ensureSpace(26);
          }
          doc.setDrawColor(225, 230, 236);
          doc.line(margin, y + 3, pageWidth - margin, y + 3);
          doc.setFillColor(32, 40, 54);
          doc.roundedRect(margin, y - 8, 4, 14, 2, 2, 'F');
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(12.5);
          doc.setTextColor(20, 20, 20);
          doc.text(text, margin + 10, y);
          y += 16;
        };

        const drawStatusPill = (label, colorRgb, x, yy, width) => {
          doc.setFillColor(colorRgb[0], colorRgb[1], colorRgb[2]);
          doc.roundedRect(x, yy, width, 16, 6, 6, 'F');
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(8.5);
          doc.setTextColor(255, 255, 255);
          doc.text(label, x + width / 2, yy + 11, { align: 'center' });
        };

        const drawCheckCards = () => {
          const checks = Array.isArray(operationalReadiness?.checks) ? operationalReadiness.checks : [];
          if (!checks.length) return;

          const cardGap = 10;
          const cardW = (maxWidth - cardGap) / 2;
          const cardH = 58;

          checks.forEach((ck, idx) => {
            const col = idx % 2;
            if (col === 0) {
              ensureSpace(cardH + 10);
            }
            const row = Math.floor(idx / 2);
            const x = margin + col * (cardW + cardGap);
            const yy = y + row * (cardH + 8);

            const passed = Boolean(ck?.passed);
            const colorRgb = passed ? [67, 160, 71] : [198, 75, 75];

            doc.setDrawColor(220, 220, 220);
            doc.setFillColor(248, 248, 248);
            doc.roundedRect(x, yy, cardW, cardH, 8, 8, 'FD');

            drawStatusPill(passed ? 'OK' : 'PERLU AKSI', colorRgb, x + cardW - 82, yy + 8, 70);

            doc.setFont('helvetica', 'bold');
            doc.setFontSize(10);
            doc.setTextColor(26, 26, 26);
            const keyText = String(ck?.key || '-').replace(/_/g, ' ').toUpperCase();
            doc.text(keyText, x + 10, yy + 18);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9);
            const noteLines = splitClamped(String(ck?.note || '-'), cardW - 20, 2);
            noteLines.forEach((line, lineIdx) => {
              doc.text(line, x + 10, yy + 34 + (lineIdx * 10));
            });

            if (idx === checks.length - 1 || (idx % 2 === 1 && row === Math.floor((checks.length - 1) / 2))) {
              y = yy + cardH + 10;
            }
          });
        };

        const parseNeg = (value) => {
          const n = Number(value);
          if (!Number.isFinite(n)) return 0;
          if (n <= 1) return n * 100;
          return n;
        };

        const drawSimpleTable = (columns, rows, rowColorSelector = null, opts = {}) => {
          const headH = Number(opts.headHeight || 23);
          const lineHeight = Number(opts.lineHeight || 10.4);
          const cellPadY = Number(opts.cellPaddingY || 5.5);
          const zebra = opts.zebra !== false;
          const captionTitle = String(opts.title || '').trim();
          const captionSubtitle = String(opts.subtitle || '').trim();

          const resolveMaxLines = (col) => {
            if (col && (col.maxLines === undefined || col.maxLines === null)) return 0;
            const n = Number(col?.maxLines);
            return Number.isFinite(n) ? n : 0;
          };

          const estimateRowHeight = (row) => {
            if (!row) return Math.max(24, (lineHeight * 1) + (cellPadY * 2));
            const cells = columns.map((col) => {
              const raw = col.getter(row);
              return splitClamped(String(raw ?? '-'), col.w - 10, resolveMaxLines(col));
            });
            const lineCount = cells.reduce((m, lines) => Math.max(m, lines.length), 1);
            return Math.max(24, lineCount * lineHeight + (cellPadY * 2));
          };

          const drawTableMetaRow = (continued = false) => {
            if (!captionTitle && !captionSubtitle) return;

            const titleText = continued ? `${captionTitle} (Lanjutan)` : captionTitle;
            const labelW = Math.max(96, Math.min(126, Number(columns?.[0]?.w || 112)));
            const contentLines = [];
            if (titleText) contentLines.push(...splitClamped(titleText, maxWidth - labelW - 14, 1));
            if (captionSubtitle) contentLines.push(...splitClamped(captionSubtitle, maxWidth - labelW - 14, 2));
            const capH = Math.max(22, (contentLines.length * 10) + 8);

            ensureSpace(capH + 2);
            doc.setFillColor(32, 40, 54);
            doc.setDrawColor(214, 220, 228);
            doc.rect(margin, y, labelW, capH, 'FD');

            doc.setFont('helvetica', 'bold');
            doc.setFontSize(9.1);
            doc.setTextColor(255, 255, 255);
            doc.text('KETERANGAN', margin + 8, y + 14);

            doc.setFillColor(242, 246, 251);
            doc.setDrawColor(214, 220, 228);
            doc.rect(margin + labelW, y, maxWidth - labelW, capH, 'FD');

            contentLines.forEach((line, idx) => {
              const isFirst = idx === 0;
              doc.setFont('helvetica', isFirst ? 'bold' : 'normal');
              doc.setFontSize(isFirst ? 9.1 : 8.2);
              doc.setTextColor(isFirst ? 32 : 90, isFirst ? 40 : 98, isFirst ? 54 : 108);
              doc.text(line, margin + labelW + 6, y + 13 + (idx * 9.4));
            });

            y += capH;
          };

          const drawHeader = () => {
            let x = margin;
            doc.setFillColor(32, 40, 54);
            doc.setDrawColor(214, 220, 228);
            doc.rect(margin, y, maxWidth, headH, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(9.1);

            columns.forEach((col) => {
              doc.rect(x, y, col.w, headH);
              const label = String(col.title || '').toUpperCase();
              const align = col.align === 'center' ? 'center' : (col.align === 'right' ? 'right' : 'left');
              const tx = align === 'center' ? (x + (col.w / 2)) : (align === 'right' ? (x + col.w - 6) : (x + 6));
              doc.text(label, tx, y + 14, { align });
              x += col.w;
            });

            y += headH;
          };

          const firstRowH = estimateRowHeight(Array.isArray(rows) && rows.length ? rows[0] : null);
          ensureSpace((captionTitle || captionSubtitle ? 30 : 0) + headH + firstRowH + 6);
          drawTableMetaRow(false);
          drawHeader();

          rows.forEach((row, ridx) => {
            const cells = columns.map((col) => {
              const raw = col.getter(row);
              return splitClamped(String(raw ?? '-'), col.w - 10, resolveMaxLines(col));
            });
            const lineCount = cells.reduce((m, lines) => Math.max(m, lines.length), 1);
            const rowH = Math.max(24, lineCount * lineHeight + (cellPadY * 2));

            ensureSpace(rowH + 2, () => {
              drawTableMetaRow(true);
              drawHeader();
            });

            const rowColor = typeof rowColorSelector === 'function' ? rowColorSelector(row, ridx) : null;
            const defaultColor = zebra
              ? (ridx % 2 === 0 ? [251, 252, 253] : [246, 248, 251])
              : [255, 255, 255];
            const fillColor = rowColor || defaultColor;

            let x = margin;
            columns.forEach((col, cidx) => {
              doc.setFillColor(fillColor[0], fillColor[1], fillColor[2]);
              doc.rect(x, y, col.w, rowH, 'F');
              doc.setDrawColor(214, 214, 214);
              doc.rect(x, y, col.w, rowH);
              doc.setTextColor(28, 28, 28);
              doc.setFont('helvetica', 'normal');
              const fontSize = Number(col.fontSize || 8.8);
              doc.setFontSize(fontSize);
              const lines = cells[cidx];
              const align = col.align === 'center' ? 'center' : (col.align === 'right' ? 'right' : 'left');
              const tx = align === 'center' ? (x + (col.w / 2)) : (align === 'right' ? (x + col.w - 5) : (x + 5));
              const baselineOffset = Math.max(7.2, fontSize * 0.9);
              const textBlockHeight = ((lines.length - 1) * lineHeight) + baselineOffset;
              const contentHeight = rowH - (cellPadY * 2);
              const topExtra = Math.max(0, (contentHeight - textBlockHeight) / 2);
              const textStartY = y + cellPadY + baselineOffset + topExtra;
              lines.forEach((line, lidx) => {
                doc.text(line, tx, textStartY + (lidx * lineHeight), { align });
              });
              x += col.w;
            });
            y += rowH;
          });

          y += 8;
        };

        drawCover();

        drawSectionTitle('1) Pemeriksaan Kesiapan (Traffic Light)');
        drawCheckCards();

        if (payload.readinessWarnings.length) {
          drawSectionTitle('2) Catatan Risiko Utama');
          payload.readinessWarnings.forEach((warn) => {
            writeBlock(`- ${warn}`, { size: 10, gap: 1 });
          });
          y += 6;
        }

        drawSectionTitle('3) Rekomendasi Segmen Aktif');
        const segmentColumns = [
          { title: 'Segmen', w: 124, getter: (r) => r.segmentName, maxLines: 2 },
          { title: 'Aspek', w: 72, getter: (r) => r.aspek, maxLines: 2 },
          { title: 'Negatif', w: 62, getter: (r) => `${r.negPct}%`, align: 'center', maxLines: 1, fontSize: 8.6 },
          { title: 'Komentar', w: 66, getter: (r) => `${r.total}`, align: 'center', maxLines: 1, fontSize: 8.6 },
          { title: 'Aksi Mingguan', w: maxWidth - (124 + 72 + 62 + 66), getter: (r) => r.text, maxLines: 0 },
        ];

        drawSimpleTable(segmentColumns, payload.segmentRows, (row) => {
          const negPct = parseNeg(row.negPct);
          if (negPct >= 40) return [255, 235, 235];
          if (negPct >= 25) return [255, 245, 222];
          return [236, 249, 236];
        }, {
          lineHeight: 10,
          cellPaddingY: 5.5,
          title: 'Tabel 1. Rekomendasi Segmen Aktif',
          subtitle: 'Daftar segmen, aspek prioritas, persentase sentimen negatif, total komentar, dan aksi mingguan yang direkomendasikan.',
        });

        if (payload.variantRows.length) {
          const currentPageNo = Number(doc.internal.getNumberOfPages() || 1);
          if (currentPageNo === 1) {
            doc.addPage();
            y = margin;
          }

          drawSectionTitle('4) Ringkasan Varian Prioritas', { topGap: 6 });
          const variantColumns = [
            { title: 'Varian', w: 132, getter: (r) => r.varian, maxLines: 2 },
            { title: 'Skor', w: 52, getter: (r) => r.score, align: 'center', maxLines: 1, fontSize: 8.6 },
            { title: 'Sampel', w: 58, getter: (r) => r.sample, align: 'center', maxLines: 1, fontSize: 8.6 },
            { title: 'Keyakinan', w: 76, getter: (r) => r.confidence, align: 'center', maxLines: 1, fontSize: 8.6 },
            { title: 'Isu Dominan', w: maxWidth - (132 + 52 + 58 + 76), getter: (r) => r.isu, maxLines: 3 },
          ];

          drawSimpleTable(variantColumns, payload.variantRows.slice(0, 6), (row) => {
            return row.sampleSufficient ? [239, 249, 239] : [255, 240, 228];
          }, {
            lineHeight: 10,
            cellPaddingY: 5.5,
            title: 'Tabel 2. Ringkasan Varian Prioritas',
            subtitle: 'Menampilkan skor kualitas, jumlah sampel komentar, tingkat keyakinan, dan isu dominan untuk setiap varian.',
          });
        }

        drawSectionTitle('5) Ringkasan Eksekusi', { topGap: 6 });
        writeBlock('Gunakan dokumen ini sebagai dasar rapat mingguan: pilih maksimal 3 aksi prioritas, tetapkan PIC, dan ukur dampak pada periode berikutnya.', { size: 10, gap: 2 });
        writeBlock('Catatan: keputusan otomatis penuh hanya disarankan saat status kesiapan = SIAP dan kualitas model/stabilitas data memenuhi ambang.', { size: 9.5, gap: 0 });

        const totalPages = doc.getNumberOfPages();
        for (let pageNo = 1; pageNo <= totalPages; pageNo++) {
          doc.setPage(pageNo);
          drawFooterWatermark(pageNo, totalPages);
        }

        const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
        doc.save(`absa_ringkasan_owner_detail_${stamp}.pdf`);
      }

      function renderTrendPeriode(items) {
        if (!trendPeriodeBody) return;
        if (!Array.isArray(items) || items.length === 0) {
          trendPeriodeBody.innerHTML = '<tr><td colspan="4" style="color:rgba(255,255,255,.65)">Belum tersedia data tren periode pada segmen ini.</td></tr>';
          return;
        }

        const rows = items.slice(-8);
        trendPeriodeBody.innerHTML = rows.map(row => {
          const periode = row.periode || '-';
          const total = Number(row.jumlah_komentar || 0);
          const neg = Number(row.negatif || 0);
          const negPct = Number(row.persen_negatif || 0).toFixed(1);
          return `
                            <tr>
                              <td>${safeHtml(periode)}</td>
                              <td>${total}</td>
                              <td>${neg}</td>
                              <td>${negPct}%</td>
                            </tr>
                          `;
        }).join('');
      }

      function renderEarlyWarning(items) {
        if (!earlyWarnBody) return;
        if (!Array.isArray(items) || items.length === 0) {
          earlyWarnBody.innerHTML = '<tr><td colspan="4" style="color:rgba(255,255,255,.65)">Belum terdapat peringatan dini pada segmen ini.</td></tr>';
          return;
        }

        const badgeClass = (lvl) => {
          const x = String(lvl || 'low').toLowerCase();
          if (x === 'high') return 'high';
          if (x === 'medium') return 'medium';
          return 'low';
        };

        earlyWarnBody.innerHTML = items.slice(0, 5).map(row => {
          const levelRaw = String(row.level || 'low').toLowerCase();
          const level = levelRaw === 'high' ? 'TINGGI' : (levelRaw === 'medium' ? 'SEDANG' : 'RENDAH');
          const klass = badgeClass(row.level);
          const indikator = safeHtml(row.indikator);
          const value = safeHtml(row.value);
          const text = safeHtml(row.text);
          return `
                            <tr>
                              <td><span class="intentBadge ${klass}">${level}</span></td>
                              <td>${indikator}</td>
                              <td>${value}</td>
                              <td><span class="quickRecoText">${text}</span></td>
                            </tr>
                          `;
        }).join('');
      }

      function renderSegmentCompare(activeKey) {
        if (!segmentCompareBody) return;

        const order = ['all', 'used', 'non_user'];
        const compareLabel = (segmentKey) => {
          if (segmentKey === 'used') return 'Sudah Menggunakan';
          if (segmentKey === 'non_user') return 'Belum Menggunakan';
          return 'Seluruh Responden';
        };
        const getTopAspek = (view) => {
          const rows = Array.isArray(view?.prioritas) ? view.prioritas : [];
          if (!rows.length) return '-';
          const best = rows[0] || {};
          const nm = String(best.aspek || '-');
          const val = Number(best.total_negatif || 0);
          return `${nm} (${val})`;
        };
        const getHighestWarning = (view) => {
          const rows = Array.isArray(view?.early_warning) ? view.early_warning : [];
          if (!rows.length) return { text: '-', klass: 'low' };
          const rank = { high: 3, medium: 2, low: 1 };
          let best = rows[0];
          for (const row of rows) {
            const cur = rank[String(row.level || 'low').toLowerCase()] || 1;
            const prev = rank[String(best.level || 'low').toLowerCase()] || 1;
            if (cur > prev) best = row;
          }
          const lvl = String(best.level || 'low').toLowerCase();
          if (lvl === 'high') return { text: 'Tinggi', klass: 'high' };
          if (lvl === 'medium') return { text: 'Sedang', klass: 'medium' };
          return { text: 'Rendah', klass: 'low' };
        };

        const html = order.map((key) => {
          const view = segmentViews[key] || {};
          const isActive = key === activeKey;
          const segName = compareLabel(key);
          const jumlah = Number(view.jumlah_komentar || 0);
          const negPct = pct(view.persen_negatif || 0);
          const topAspek = getTopAspek(view);
          const ew = getHighestWarning(view);
          const rowStyle = isActive ? ' style="background:rgba(214,181,74,.13);"' : '';
          const segText = isActive ? `<b>${segName}</b>` : segName;
          return `
                            <tr${rowStyle}>
                              <td>${segText}</td>
                              <td>${jumlah}</td>
                              <td>${negPct}</td>
                              <td>${safeHtml(topAspek)}</td>
                              <td><span class="intentBadge ${ew.klass}">${ew.text}</span></td>
                            </tr>
                          `;
        }).join('');

        segmentCompareBody.innerHTML = html;
      }

      function renderTopIsu(items) {
        if (!topIsuBody) return;
        if (!Array.isArray(items) || items.length === 0) {
          topIsuBody.innerHTML = '<tr><td colspan="3" style="color:rgba(255,255,255,.65)">Belum tersedia data pada segmen ini.</td></tr>';
          return;
        }
        topIsuBody.innerHTML = items.map(row => `
                            <tr>
                              <td>${safeHtml(row.aspek)}</td>
                              <td>${safeHtml(row.isu)}</td>
                              <td>${Number(row.frekuensi || 0)}</td>
                            </tr>
                          `).join('');
      }

      function renderTopKata(items) {
        if (!topKataChips) return;
        if (!Array.isArray(items) || items.length === 0) {
          topKataChips.innerHTML = '<div class="mini">Belum terdapat kata kunci terdeteksi.</div>';
          return;
        }
        topKataChips.innerHTML = items.slice(0, 4).map(row => `
                            <div class="chip">
                              <span>${safeHtml(row.kata)}</span>
                              <b>${Number(row.frekuensi || 0)}</b>
                            </div>
                          `).join('');
      }

      function renderSentimenAspek(items) {
        const rows = Array.isArray(items) ? items.slice(0, 3) : [];
        const safeRows = rows.length ? rows : [
          { aspek: 'Aroma', positif: 0, negatif: 0, total: 0, persen_negatif: 0 },
          { aspek: 'Kemasan', positif: 0, negatif: 0, total: 0, persen_negatif: 0 },
          { aspek: 'Ketahanan', positif: 0, negatif: 0, total: 0, persen_negatif: 0 }
        ];

        const first = safeRows[0] || { persen_negatif: 0, total: 0, positif: 0 };
        let donutPct = Number(first.persen_negatif || 0);
        if (donutPct <= 0 && Number(first.total || 0) > 0) {
          donutPct = (Number(first.positif || 0) / Number(first.total || 1)) * 100;
        }
        donutPct = Math.max(0, Math.min(100, Number(donutPct.toFixed(1))));

        if (sentimDonut) sentimDonut.style.setProperty('--pct', `${donutPct}%`);
        if (sentimDonutText) sentimDonutText.textContent = `${donutPct}%`;

        if (sentimBreakdown) {
          sentimBreakdown.innerHTML = safeRows.map(row => {
            const total = Number(row.total || 0);
            let pct = Number(row.persen_negatif || 0);
            if (pct <= 0 && total > 0) {
              pct = (Number(row.positif || 0) / total) * 100;
            }
            return `
                                <div class="brow">
                                  <div class="k">${safeHtml(row.aspek)}</div>
                                  <div class="v">${pct.toFixed(1)}%</div>
                                </div>
                              `;
          }).join('');
        }

        if (sentimBars) {
          const maxCount = safeRows.reduce((m, r) => Math.max(m, Number(r.total || 0)), 0);
          sentimBars.innerHTML = safeRows.map(row => {
            const ct = Number(row.total || 0);
            const width = maxCount > 0 ? Math.max(3, Math.round((ct / maxCount) * 100)) : 0;
            return `
                                <div class="barRow">
                                  <div class="name">${safeHtml(row.aspek)}</div>
                                  <div class="bar"><div class="fill" style="width:${width}%"></div></div>
                                  <div class="p">${ct}</div>
                                </div>
                              `;
          }).join('');
        }
      }

      function renderPrioritas(items) {
        if (!prioritasList) return;
        if (!Array.isArray(items) || items.length === 0) {
          prioritasList.innerHTML = '<div class="mini">Belum tersedia prioritas pada segmen ini.</div>';
          return;
        }

        const rows = items.slice(0, 3);
        const maxNeg = rows.reduce((m, r) => Math.max(m, Number(r.total_negatif || 0)), 0);
        prioritasList.innerHTML = rows.map(row => {
          const val = Number(row.total_negatif || 0);
          const width = maxNeg > 0 ? Math.max(3, Math.round((val / maxNeg) * 100)) : 0;
          return `
                              <div class="prioRow">
                                <div class="nm">${safeHtml(row.aspek)}</div>
                                <div class="prioBar"><div class="prioFill" style="width:${width}%"></div></div>
                                <div class="prioVal">${val}</div>
                              </div>
                            `;
        }).join('');
      }

      function renderRekomendasi(items) {
        if (!segmentRekomList) return;
        if (!Array.isArray(items) || items.length === 0) {
          segmentRekomList.innerHTML = '<div class="mini" style="margin-top:8px">Belum tersedia rekomendasi untuk segmen ini.</div>';
          return;
        }

        const toTitleCase = (val) => {
          const raw = String(val || '-').replace(/_/g, ' ').trim();
          if (!raw) return '-';
          return raw.toLowerCase().replace(/\b\w/g, (ch) => ch.toUpperCase());
        };

        const normalizeSentence = (val) => {
          const raw = String(val || '-').replace(/\s+/g, ' ').trim();
          if (!raw || raw === '-') return '-';
          return raw.charAt(0).toUpperCase() + raw.slice(1);
        };

        const buildMetaLine = (row) => {
          const kpi = normalizeSentence(row.kpi_target || '-');
          const horizon = Number(row.horizon_hari || 0);
          const confidenceRaw = String(row.confidence || '-').trim().toLowerCase();
          const confidence = confidenceRaw === 'high'
            ? 'Tinggi'
            : (confidenceRaw === 'medium' ? 'Sedang' : (confidenceRaw === 'low' ? 'Rendah' : '-'));
          const parts = [];
          if (kpi && kpi !== '-') parts.push(`KPI: ${kpi}`);
          if (horizon > 0) parts.push(`Jangka Waktu: ${horizon} hari`);
          if (confidence && confidence !== '-') parts.push(`Tingkat Keyakinan: ${confidence}`);
          return parts.length ? parts.join(' • ') : '-';
        };

        segmentRekomList.innerHTML = items.slice(0, 3).map(row => `
                            <div class="rekomItem">
                              <div class="ricon">★</div>
                              <div>
                                <p class="ttl">${safeHtml(toTitleCase(row.aspek))}</p>
                                <p class="txt">${safeHtml(normalizeSentence(row.text))}</p>
                                <p class="mini" style="margin-top:4px">${safeHtml(buildMetaLine(row))}</p>
                              </div>
                            </div>
                          `).join('');
      }

      function renderDrilldown(segmentKey, aspekKey) {
        const view = segmentViews[segmentKey] || {};
        const drill = (view.drilldown_aspek || {})[aspekKey] || {};
        const posItems = Array.isArray(drill.positif) && drill.positif.length ? drill.positif : ['Belum tersedia data.'];
        const negItems = Array.isArray(drill.negatif) && drill.negatif.length ? drill.negatif : ['Belum tersedia data.'];
        const posCount = Number(drill.jumlah_positif || 0);
        const negCount = Number(drill.jumlah_negatif || 0);

        if (posList) {
          posList.innerHTML = posItems.map(x => `<li>${safeHtml(x)}</li>`).join('');
        }
        if (negList) {
          negList.innerHTML = negItems.map(x => `<li>${safeHtml(x)}</li>`).join('');
        }
        if (posCountEl) {
          posCountEl.textContent = `(${Number.isFinite(posCount) ? posCount : 0})`;
        }
        if (negCountEl) {
          negCountEl.textContent = `(${Number.isFinite(negCount) ? negCount : 0})`;
        }
      }

      function getTopSegmentAspects(view) {
        const recs = Array.isArray(view?.rekomendasi) ? view.rekomendasi : [];
        const seen = new Set();
        const out = [];
        recs.forEach((row) => {
          const key = String(row?.aspek || '').trim().toLowerCase();
          if (!key) return;
          if (seen.has(key)) return;
          seen.add(key);
          out.push(key);
        });
        return out.slice(0, 3);
      }

      function detectIssueAspect(issueText) {
        const issue = String(issueText || '').trim().toLowerCase();
        if (!issue || issue === '-') return null;

        const issueAspectMap = {
          aroma: ['menyengat', 'nyengat', 'pusing', 'tajam', 'bau', 'eneg', 'manis', 'wangi', 'harum'],
          ketahanan: ['cepat', 'hilang', 'ilang', 'pudar', 'awet', 'tahan', 'lama', 'ketahanan'],
          kemasan: ['bocor', 'tumpah', 'rembes', 'rusak', 'pecah', 'patah', 'retak', 'longgar', 'lepas', 'tutup', 'nozzle', 'spray', 'semprot', 'sprayer'],
        };

        for (const [aspect, keywords] of Object.entries(issueAspectMap)) {
          if (keywords.some((kw) => issue.includes(kw))) {
            return aspect;
          }
        }
        return null;
      }

      function computeVariantAlignment(row, topAspects) {
        const currentTop = Array.isArray(topAspects) ? topAspects.filter(Boolean) : [];
        if (!currentTop.length) {
          return { key: 'partial', label: 'Sebagian', score: 1 };
        }

        const dominantAspect = detectIssueAspect(row?.isu_dominan);
        if (dominantAspect && currentTop.includes(dominantAspect)) {
          return { key: 'aligned', label: 'Selaras', score: 2 };
        }

        if (dominantAspect && ['aroma', 'ketahanan', 'kemasan'].includes(dominantAspect)) {
          return { key: 'partial', label: 'Sebagian', score: 1 };
        }

        return { key: 'diverged', label: 'Menyimpang', score: 0 };
      }

      function renderVariantAlignmentQueue(view) {
        if (!variantRankBody || !Array.isArray(variantRankingsData) || !variantRankingsData.length) return;

        const topAspects = getTopSegmentAspects(view);
        const rows = variantRankingsData.map((row) => {
          const alignment = computeVariantAlignment(row, topAspects);
          return { ...row, _alignment: alignment };
        });

        rows.sort((a, b) => {
          const s = Number(b?._alignment?.score || 0) - Number(a?._alignment?.score || 0);
          if (s !== 0) return s;
          return Number(a?.peringkat || 999) - Number(b?.peringkat || 999);
        });

        variantRankBody.innerHTML = rows.map((row) => {
          const badgeKey = row?._alignment?.key || 'partial';
          const badgeLabel = row?._alignment?.label || 'Sebagian';
          const isuRaw = row.isu_dominan || '-';
          const isuSafe = escapeHtml(isuRaw);
          return `
                        <tr>
                          <td>${Number(row.peringkat || 0) || '-'}</td>
                          <td>${escapeHtml(row.varian || '-')}</td>
                          <td>${Number(row.skor_kualitas || 0).toFixed(1)}</td>
                          <td>${Number(row.persen_negatif || 0).toFixed(1)}%</td>
                          <td>${Math.max(0, Math.round(Number(row.total_komentar || 0)))}</td>
                          <td><span class="alignBadge ${badgeKey}">${badgeLabel}</span></td>
                        <td><span class="variantIsuText" title="${isuSafe}">${isuSafe}</span></td>
                        </tr>
                      `;
        }).join('');

        if (variantSyncHint) {
          if (!topAspects.length) {
            variantSyncHint.textContent = 'Prioritas segmen aktif belum terbaca. Urutan varian memakai dasar skor kualitas.';
          } else {
            const readable = topAspects.map((x) => String(x || '').replace(/\b\w/g, (m) => m.toUpperCase())).join(', ');
            variantSyncHint.textContent = `Prioritas segmen aktif: ${readable}. Urutan varian memprioritaskan status Selaras terlebih dahulu.`;
          }
        }
      }

      function renderSegment(segmentKey) {
        const view = segmentViews[segmentKey];
        if (!view) return;

        activeSegment = segmentKey;

        animateNumber(jumlahEl, Number(view.jumlah_komentar || 0), { decimals: 0, duration: 440 });
        animateNumber(negatifEl, Number(view.persen_negatif || 0) * 100, { decimals: 1, suffix: '%', duration: 390 });
        if (labelEl) labelEl.textContent = `Segmen aktif: ${segmentLabel(segmentKey)}`;
        renderPanelContext(segmentKey);

        renderTopIsu(view.top_isu || []);
        renderTopKata(view.top_kata || []);
        renderTrendPeriode(view.trend_periode || []);
        renderEarlyWarning(view.early_warning || []);
        renderSegmentCompare(segmentKey);
        renderSentimenAspek(view.sentimen_per_aspek || []);
        renderPrioritas(view.prioritas || []);
        renderRekomendasi(view.rekomendasi || []);
        renderVariantAlignmentQueue(view);
        if (segmentKey !== 'non_user') {
          renderDrilldown(segmentKey, activeAspek);
        }

        const variantEnabled = view.variant_enabled !== undefined
          ? Boolean(view.variant_enabled)
          : segmentKey !== 'non_user';
        if (variantScopedArea) variantScopedArea.style.display = variantEnabled ? '' : 'none';
        if (variantScopedHint) variantScopedHint.style.display = variantEnabled ? 'none' : '';

        const scopedEnabled = segmentKey !== 'non_user';
        if (healthScopedArea) healthScopedArea.style.display = scopedEnabled ? '' : 'none';
        if (healthScopedHint) healthScopedHint.style.display = scopedEnabled ? 'none' : '';
        if (sentimScopedArea) sentimScopedArea.style.display = scopedEnabled ? '' : 'none';
        if (sentimScopedHint) sentimScopedHint.style.display = scopedEnabled ? 'none' : '';
        if (isuScopedArea) isuScopedArea.style.display = scopedEnabled ? '' : 'none';
        if (isuScopedHint) isuScopedHint.style.display = scopedEnabled ? 'none' : '';
        if (drillScopedArea) drillScopedArea.style.display = scopedEnabled ? '' : 'none';
        if (drillScopedHint) drillScopedHint.style.display = scopedEnabled ? 'none' : '';
        if (prioScopedArea) prioScopedArea.style.display = scopedEnabled ? '' : 'none';
        if (prioScopedHint) prioScopedHint.style.display = scopedEnabled ? 'none' : '';
        if (nonUserOnlySection) nonUserOnlySection.style.display = segmentKey === 'non_user' ? '' : 'none';

        animateContentSwap([
          topIsuBody,
          topKataChips,
          trendPeriodeBody,
          earlyWarnBody,
          segmentCompareBody,
          sentimBreakdown,
          sentimBars,
          prioritasList,
          segmentRekomList
        ]);

        segButtons.forEach(btn => {
          btn.classList.toggle('active', btn.dataset.segment === segmentKey);
        });

        if (typeof window.requestAnimationFrame === 'function') {
          window.requestAnimationFrame(syncAllTableScrollHints);
        } else {
          syncAllTableScrollHints();
        }
      }

      segButtons.forEach(btn => {
        btn.addEventListener('click', () => renderSegment(btn.dataset.segment));
      });

      aspekButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          activeAspek = btn.dataset.aspek;
          aspekButtons.forEach(x => x.classList.toggle('active', x.dataset.aspek === activeAspek));
          renderDrilldown(activeSegment, activeAspek);
          animateContentSwap([posList, negList]);
        });
      });

      if (exportManagerPdfBtn) {
        exportManagerPdfBtn.addEventListener('click', exportManagerialPdf);
      }

      tableScrollAreas.forEach((area) => {
        area.addEventListener('scroll', () => syncTableScrollHint(area), { passive: true });
      });

      window.addEventListener('resize', syncAllTableScrollHints, { passive: true });

      renderSegment(activeSegment);
      animateDashboardEntrance();
      aspekButtons.forEach(x => x.classList.toggle('active', x.dataset.aspek === activeAspek));
      syncAllTableScrollHints();
    })();
  </script>
@endif

@if(!empty($variants))
  <script>
    (function () {
      const recs = @json($variantRecs);
      const variantRankings = @json($variantRankings);
      const select = document.getElementById('variantSelect');
      const aromaEl = document.getElementById('recoAromaText');
      const ketahananEl = document.getElementById('recoKetahananText');
      const aromaMetaEl = document.getElementById('recoAromaMeta');
      const ketahananMetaEl = document.getElementById('recoKetahananMeta');
      const variantCommentInfoEl = document.getElementById('variantCommentInfo');
      if (!select || !aromaEl || !ketahananEl) return;

      const sampleByVariant = Array.isArray(variantRankings)
        ? variantRankings.reduce((acc, row) => {
          const key = String(row?.varian || '').trim();
          if (!key) return acc;
          acc[key] = Number(row?.total_komentar || 0);
          return acc;
        }, {})
        : {};

      const fmtInt = (n) => {
        const x = Number(n || 0);
        if (!Number.isFinite(x)) return '0';
        return String(Math.max(0, Math.round(x)));
      };

      function fmtMeta(plan) {
        const p = plan || {};
        const kpi = String(p.kpi_target || '-').trim();
        const horizon = Number(p.horizon_hari || 0);
        const confidenceRaw = String(p.confidence || '-').trim().toLowerCase();
        const confidence = confidenceRaw === 'high'
          ? 'Tinggi'
          : (confidenceRaw === 'medium' ? 'Sedang' : (confidenceRaw === 'low' ? 'Rendah' : '-'));
        const parts = [];
        if (kpi && kpi !== '-') parts.push(`KPI: ${kpi}`);
        if (horizon > 0) parts.push(`Jangka Waktu: ${horizon} hari`);
        if (confidence && confidence !== '-') parts.push(`Tingkat Keyakinan: ${confidence}`);
        return parts.length ? parts.join(' • ') : '-';
      }

      function updateReco() {
        const v = select.value;
        const data = recs[v] || {};
        aromaEl.textContent = data.aroma || '-';
        ketahananEl.textContent = data.ketahanan || '-';
        if (aromaMetaEl) aromaMetaEl.textContent = fmtMeta(data.aroma_plan);
        if (ketahananMetaEl) ketahananMetaEl.textContent = fmtMeta(data.ketahanan_plan);
        if (variantCommentInfoEl) {
          const totalKomentar = sampleByVariant[v];
          variantCommentInfoEl.textContent = `Jumlah komentar varian terpilih: ${Number.isFinite(totalKomentar) ? fmtInt(totalKomentar) : '-'}`;
        }
      }

      select.addEventListener('change', updateReco);
      updateReco();
    })();
  </script>
@endif

<script>
  (function () {
    const form = document.getElementById('analyzeForm');
    const submitBtn = document.getElementById('analyzeSubmitBtn');
    const overlay = document.getElementById('submitLoadingOverlay');
    const loadingTitleEl = document.getElementById('submitLoadingTitle');
    const loadingSubEl = document.getElementById('submitLoadingSub');
    const loadingStepFillEl = document.getElementById('submitLoadingStepFill');
    const loadingStepMetaEl = document.getElementById('submitLoadingStepMeta');
    const resetEstimateBtn = document.getElementById('resetLoadingEstimateBtn');
    const resetEstimateInfo = document.getElementById('resetLoadingEstimateInfo');
    if (!form || !submitBtn) return;

    const labelEl = submitBtn.querySelector('.btnLabel');
    const spinnerEl = submitBtn.querySelector('.btnSpinner');
    const defaultLabel = labelEl ? labelEl.textContent : 'Analisis';
    const defaultLoadingTitle = loadingTitleEl ? loadingTitleEl.textContent : 'Memproses analisis…';
    const defaultLoadingSub = loadingSubEl
      ? loadingSubEl.textContent
      : 'Sedang menyiapkan hasil dashboard. Mohon tunggu sebentar.';
    const loadingEstimateKey = 'absa_loading_estimate_ms_v1';
    const loadingPendingKey = 'absa_loading_pending_start_v1';
    const loadingDebugKey = 'absa_loading_debug_v1';
    const defaultEstimateMs = 2600;
    const minEstimateMs = 1400;
    const maxEstimateMs = 15000;
    const loadingStepWeights = [0.2, 0.33, 0.32, 0.15];
    const loadingSteps = [
      {
        title: 'Memvalidasi tautan data…',
        sub: 'Memastikan URL Google Sheets/CSV dapat diakses.'
      },
      {
        title: 'Mengunduh dan membaca data…',
        sub: 'Data responden sedang dipersiapkan untuk proses analisis.'
      },
      {
        title: 'Menjalankan analisis sentimen…',
        sub: 'Model sedang menghitung wawasan per aspek dan segmen.'
      },
      {
        title: 'Menyusun hasil dashboard…',
        sub: 'Visual dan ringkasan hasil sedang dirapikan.'
      }
    ];
    let loadingStepTimer = null;
    let loadingStepIndex = 0;
    let resetEstimateTimer = null;

    const loadingDebugEnabled = (() => {
      try {
        const params = new URLSearchParams(window.location.search || '');
        const fromQuery = params.get('loadingDebug');
        if (fromQuery === '1') {
          window.localStorage.setItem(loadingDebugKey, '1');
          return true;
        }
        if (fromQuery === '0') {
          window.localStorage.removeItem(loadingDebugKey);
          return false;
        }
        return window.localStorage.getItem(loadingDebugKey) === '1';
      } catch (_) {
        return false;
      }
    })();

    function logLoadingDebug(eventName, payload = {}) {
      if (!loadingDebugEnabled || !window.console || typeof window.console.info !== 'function') return;
      window.console.info('[ABSA Loading]', eventName, payload);
    }

    if (loadingDebugEnabled) {
      logLoadingDebug('debug_enabled', {
        hint: 'Use ?loadingDebug=0 to disable',
      });
    }

    function clamp(value, min, max) {
      return Math.max(min, Math.min(max, value));
    }

    function readEstimatedTotalMs() {
      try {
        const raw = window.localStorage.getItem(loadingEstimateKey);
        const parsed = Number(raw);
        if (Number.isFinite(parsed)) {
          const bounded = clamp(Math.round(parsed), minEstimateMs, maxEstimateMs);
          logLoadingDebug('estimate_read', { source: 'localStorage', valueMs: bounded });
          return bounded;
        }
      } catch (_) {
      }
      logLoadingDebug('estimate_read', { source: 'default', valueMs: defaultEstimateMs });
      return defaultEstimateMs;
    }

    function renderEstimateInfo(extraText = '') {
      if (!resetEstimateInfo) return;
      const sec = (readEstimatedTotalMs() / 1000).toFixed(1);
      const baseText = `Estimasi saat ini ~${sec} dtk`;
      resetEstimateInfo.textContent = extraText ? `${baseText} • ${extraText}` : baseText;
    }

    function buildStepDurations(totalMs) {
      const base = loadingStepWeights.map((weight) => Math.round(totalMs * weight));
      return [
        clamp(base[0], 500, 2200),
        clamp(base[1], 850, 3600),
        clamp(base[2], 950, 4200),
        clamp(base[3], 700, 2600)
      ];
    }

    function updateEstimateFromPendingSubmit() {
      try {
        const pendingRaw = window.sessionStorage.getItem(loadingPendingKey);
        if (!pendingRaw) return;
        window.sessionStorage.removeItem(loadingPendingKey);

        const startedAt = Number(pendingRaw);
        if (!Number.isFinite(startedAt) || startedAt <= 0) return;

        const elapsed = Date.now() - startedAt;
        if (!Number.isFinite(elapsed) || elapsed < 350 || elapsed > 180000) return;

        const prev = readEstimatedTotalMs();
        const calibrated = Math.round((prev * 0.72) + (elapsed * 0.28));
        const bounded = clamp(calibrated, minEstimateMs, maxEstimateMs);
        window.localStorage.setItem(loadingEstimateKey, String(bounded));
        logLoadingDebug('estimate_calibrated', {
          elapsedMs: elapsed,
          prevMs: prev,
          nextMs: bounded,
        });
        renderEstimateInfo();
      } catch (_) {
      }
    }

    updateEstimateFromPendingSubmit();
    renderEstimateInfo();

    function applyLoadingStep(index) {
      const step = loadingSteps[index] || loadingSteps[0];
      if (loadingTitleEl) loadingTitleEl.textContent = step.title;
      if (loadingSubEl) loadingSubEl.textContent = step.sub;

      const totalSteps = loadingSteps.length;
      const safeIndex = clamp(Number(index || 0), 0, totalSteps - 1);
      const progressPct = Math.round(((safeIndex + 1) / totalSteps) * 100);
      if (loadingStepFillEl) {
        loadingStepFillEl.style.width = `${progressPct}%`;
      }
      if (loadingStepMetaEl) {
        loadingStepMetaEl.textContent = `Tahap ${safeIndex + 1}/${totalSteps} • ${progressPct}%`;
      }
    }

    function startLoadingSteps() {
      if (loadingStepTimer) {
        window.clearTimeout(loadingStepTimer);
        loadingStepTimer = null;
      }
      loadingStepIndex = 0;
      const estimatedTotalMs = readEstimatedTotalMs();
      const stepDurations = buildStepDurations(estimatedTotalMs);
      logLoadingDebug('steps_start', {
        estimateMs: estimatedTotalMs,
        stepDurationsMs: stepDurations,
      });

      const runNextStep = () => {
        applyLoadingStep(loadingStepIndex);
        logLoadingDebug('step_show', {
          index: loadingStepIndex,
          title: (loadingSteps[loadingStepIndex] || loadingSteps[0]).title,
        });
        const isLastStep = loadingStepIndex >= loadingSteps.length - 1;
        if (isLastStep) {
          loadingStepTimer = null;
          return;
        }

        const waitMs = Number(stepDurations[loadingStepIndex] || 1200);
        loadingStepTimer = window.setTimeout(() => {
          loadingStepIndex += 1;
          runNextStep();
        }, waitMs);
      };

      runNextStep();
    }

    function stopLoadingSteps() {
      if (loadingStepTimer) {
        window.clearTimeout(loadingStepTimer);
        loadingStepTimer = null;
      }
      logLoadingDebug('steps_stop');
      loadingStepIndex = 0;
      if (loadingStepFillEl) loadingStepFillEl.style.width = '0%';
      if (loadingStepMetaEl) loadingStepMetaEl.textContent = `Tahap 0/${loadingSteps.length}`;
      if (loadingTitleEl) loadingTitleEl.textContent = defaultLoadingTitle;
      if (loadingSubEl) loadingSubEl.textContent = defaultLoadingSub;
    }

    function setLoading(active) {
      document.body.classList.toggle('is-submitting', Boolean(active));
      if (overlay) overlay.setAttribute('aria-hidden', active ? 'false' : 'true');

      submitBtn.disabled = Boolean(active);
      submitBtn.classList.toggle('isLoading', Boolean(active));
      if (active) {
        submitBtn.setAttribute('aria-busy', 'true');
      } else {
        submitBtn.removeAttribute('aria-busy');
      }

      if (labelEl) {
        labelEl.textContent = active ? 'Memproses...' : defaultLabel;
      }
      if (spinnerEl) {
        spinnerEl.hidden = !active;
      }

      if (active) {
        startLoadingSteps();
      } else {
        stopLoadingSteps();
      }

      logLoadingDebug('loading_state', { active });
    }

    form.addEventListener('submit', function (event) {
      if (form.dataset.submitting === '1') {
        event.preventDefault();
        return;
      }

      event.preventDefault();
      form.dataset.submitting = '1';

      try {
        window.sessionStorage.setItem(loadingPendingKey, String(Date.now()));
        logLoadingDebug('submit_marked_pending');
      } catch (_) {
      }

      setLoading(true);

      const submitNow = () => HTMLFormElement.prototype.submit.call(form);
      if (typeof window.requestAnimationFrame === 'function') {
        window.requestAnimationFrame(submitNow);
      } else {
        window.setTimeout(submitNow, 0);
      }
    });

    if (resetEstimateBtn) {
      resetEstimateBtn.addEventListener('click', function () {
        try {
          window.localStorage.removeItem(loadingEstimateKey);
          window.sessionStorage.removeItem(loadingPendingKey);
        } catch (_) {
        }

        logLoadingDebug('estimate_reset');

        renderEstimateInfo('Direset ke default');

        resetEstimateBtn.disabled = true;
        resetEstimateBtn.textContent = 'Sudah direset';

        if (resetEstimateTimer) {
          window.clearTimeout(resetEstimateTimer);
        }
        resetEstimateTimer = window.setTimeout(() => {
          resetEstimateBtn.disabled = false;
          resetEstimateBtn.textContent = 'Reset estimasi loading';
          renderEstimateInfo();
          resetEstimateTimer = null;
        }, 1400);
      });
    }

    window.addEventListener('pageshow', function (event) {
      if (!event.persisted) return;
      form.dataset.submitting = '0';
      setLoading(false);
      renderEstimateInfo();
    });
  })();
</script>

<script>
  (function () {
    const toggleBtn = document.getElementById('compactModeBtn');
    const resetBtn = document.getElementById('resetCompactModeBtn');
    if (!toggleBtn) return;

    const storageKey = 'absa_mobile_compact';
    const compactMedia = window.matchMedia('(max-width: 360px)');

    function applyMode(isCompact) {
      document.body.classList.toggle('mobile-compact', Boolean(isCompact));
      toggleBtn.setAttribute('aria-pressed', isCompact ? 'true' : 'false');
      toggleBtn.textContent = isCompact ? 'Compact' : 'Normal';
    }

    const savedMode = window.localStorage.getItem(storageKey);
    if (savedMode === '1' || savedMode === '0') {
      applyMode(savedMode === '1');
    } else {
      applyMode(compactMedia.matches);
    }

    toggleBtn.addEventListener('click', function () {
      const nextMode = !document.body.classList.contains('mobile-compact');
      applyMode(nextMode);
      window.localStorage.setItem(storageKey, nextMode ? '1' : '0');
    });

    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        window.localStorage.removeItem(storageKey);
        applyMode(compactMedia.matches);
      });
    }

    if (compactMedia && typeof compactMedia.addEventListener === 'function') {
      compactMedia.addEventListener('change', function (event) {
        const saved = window.localStorage.getItem(storageKey);
        if (saved !== '1' && saved !== '0') {
          applyMode(Boolean(event.matches));
        }
      });
    }
  })();
</script>

<script>
  (function () {
    const topBtn = document.getElementById('backTopBtn');
    if (!topBtn) return;

    const toggleThreshold = 520;

    function syncButton() {
      const y = window.scrollY || window.pageYOffset || 0;
      topBtn.classList.toggle('show', y > toggleThreshold);
    }

    topBtn.addEventListener('click', function () {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        window.scrollTo(0, 0);
        return;
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', syncButton, { passive: true });
    window.addEventListener('resize', syncButton, { passive: true });
    syncButton();
  })();
</script>

</html>