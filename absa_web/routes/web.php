<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AbsaController;

Route::get('/', [AbsaController::class, 'index'])->name('absa.index');
Route::post('/absa/analyze', [AbsaController::class, 'analyze'])
    ->middleware('throttle:absa-analyze')
    ->name('absa.analyze');
Route::get('/absa/analyze', function () {
    return redirect()->route('absa.index');
});
