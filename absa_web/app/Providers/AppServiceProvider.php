<?php

namespace App\Providers;

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        RateLimiter::for('absa-analyze', function (Request $request) {
            $maxPerMinute = max(1, (int) env('ABSA_ANALYZE_RATE_LIMIT_PER_MINUTE', 12));

            return [
                Limit::perMinute($maxPerMinute)
                    ->by((string) $request->ip())
                    ->response(function () use ($request) {
                        if ($request->expectsJson()) {
                            return response()->json([
                                'message' => 'Terlalu banyak request analisis. Coba lagi beberapa saat.',
                            ], 429);
                        }

                        return redirect()->route('absa.index')
                            ->with('error', 'Terlalu banyak request analisis. Coba lagi beberapa saat.');
                    }),
            ];
        });
    }
}
