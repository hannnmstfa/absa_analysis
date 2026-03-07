<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class AbsaController extends Controller
{
    public function index()
    {
        $opsKeyRequired = trim((string) env('ABSA_DASHBOARD_KEY', '')) !== '';

        return view('absa.dashboard', [
            'result' => null,
            'error' => session('error'),
            'opsKeyRequired' => $opsKeyRequired,
        ]);
    }

    public function analyze(Request $request)
    {
        $opsKeyRequired = trim((string) env('ABSA_DASHBOARD_KEY', '')) !== '';

        $request->validate([
            'sheet_csv_url' => [
                'required',
                'string',
                'max:500',
                'regex:/docs\.google\.com\/spreadsheets/i',
            ],
            'dashboard_key' => ['nullable', 'string', 'max:200'],
        ]);

        $requiredOpsKey = trim((string) env('ABSA_DASHBOARD_KEY', ''));
        $providedOpsKey = trim((string) ($request->header('X-ABSA-KEY') ?? $request->input('dashboard_key', '')));
        if ($requiredOpsKey !== '' && ($providedOpsKey === '' || !hash_equals($requiredOpsKey, $providedOpsKey))) {
            return view('absa.dashboard', [
                'result' => null,
                'error' => 'Akses ditolak: kunci operasional tidak valid.',
                'opsKeyRequired' => $opsKeyRequired,
            ]);
        }

        // batasi waktu proses agar worker tidak menggantung tanpa batas.
        set_time_limit(240);

        $base = rtrim(env('ABSA_API_BASE_URL', 'http://127.0.0.1:8967'), '/');

        try {
            $resp = Http::timeout(180)      // tunggu max 180 detik
                ->connectTimeout(20)
                ->retry(2, 1000)            // retry kalau putus
                ->post($base . '/analyze', [
                    'sheet_csv_url' => trim($request->sheet_csv_url),
                ]);

            if (!$resp->successful()) {
                $apiErr = $resp->json('detail');
                if (!is_string($apiErr) || trim($apiErr) === '') {
                    $apiErr = substr((string) $resp->body(), 0, 300);
                }

                return view('absa.dashboard', [
                    'result' => null,
                    'error' => 'API error: ' . $resp->status() . ' - ' . $apiErr,
                    'opsKeyRequired' => $opsKeyRequired,
                ]);
            }

            return view('absa.dashboard', [
                'result' => $resp->json(),
                'error' => null,
                'opsKeyRequired' => $opsKeyRequired,
            ]);
        } catch (\Throwable $e) {
            return view('absa.dashboard', [
                'result' => null,
                'error' => 'Request gagal: ' . $e->getMessage(),
                'opsKeyRequired' => $opsKeyRequired,
            ]);
        }
    }
}
