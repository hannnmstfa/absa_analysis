<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class AbsaController extends Controller
{
    public function index()
    {
        return view('absa.dashboard', [
            'result' => null,
            'error' => session('error'),
        ]);
    }

    public function analyze(Request $request)
    {
        $request->validate([
            'sheet_csv_url' => 'required|string',
        ]);

        // supaya PHP tidak stop di 60 detik
        set_time_limit(0);

        $base = rtrim(env('ABSA_API_BASE_URL', 'http://127.0.0.1:8000'), '/');

        try {
            $resp = Http::timeout(180)      // tunggu max 180 detik
                ->connectTimeout(20)
                ->retry(2, 1000)            // retry kalau putus
                ->post($base . '/analyze', [
                    'sheet_csv_url' => trim($request->sheet_csv_url),
                ]);

            if (!$resp->successful()) {
                return view('absa.dashboard', [
                    'result' => null,
                    'error' => 'API error: ' . $resp->status() . ' - ' . substr($resp->body(), 0, 500),
                ]);
            }

            return view('absa.dashboard', [
                'result' => $resp->json(),
                'error' => null,
            ]);
        } catch (\Throwable $e) {
            return view('absa.dashboard', [
                'result' => null,
                'error' => 'Request gagal: ' . $e->getMessage(),
            ]);
        }
    }
}
