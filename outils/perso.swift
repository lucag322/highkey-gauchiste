import Foundation
import Vision
import CoreImage
import AppKit
// usage : perso <dossier_png> <dossier_sortie> <x> <y>   (x, y normalisés, origine en HAUT à gauche)
// Écrit deux masques gris par image : <sortie>/i/<f> = instance Vision de la personne qui contient le point
// (sinon la plus proche), <sortie>/p/<f> = segmentation personne « accurate ». decoupe.py les croise.
let a = CommandLine.arguments
let inDir = URL(fileURLWithPath: a[1]), outDir = URL(fileURLWithPath: a[2])
let px = Double(a[3])!, py = Double(a[4])!
for s in ["i", "p"] { try? FileManager.default.createDirectory(at: outDir.appendingPathComponent(s), withIntermediateDirectories: true) }
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".png") }.sorted()
let ctx = CIContext(), gray = CGColorSpaceCreateDeviceGray()
func write(_ pb: CVPixelBuffer, _ W: Int, _ H: Int, _ to: URL) throws {
    var ci = CIImage(cvPixelBuffer: pb)
    ci = ci.transformed(by: CGAffineTransform(scaleX: CGFloat(W) / ci.extent.width, y: CGFloat(H) / ci.extent.height))
    try ctx.writePNGRepresentation(of: ci, to: to, format: .L8, colorSpace: gray)
}
for f in files {
    let url = inDir.appendingPathComponent(f)
    let src = CIImage(contentsOf: url)!
    let W = Int(src.extent.width), H = Int(src.extent.height)
    let h = VNImageRequestHandler(url: url)
    let inst = VNGeneratePersonInstanceMaskRequest()
    let seg = VNGeneratePersonSegmentationRequest(); seg.qualityLevel = .accurate; seg.outputPixelFormat = kCVPixelFormatType_OneComponent8
    try h.perform([inst, seg])
    if let pb = seg.results?.first?.pixelBuffer { try write(pb, W, H, outDir.appendingPathComponent("p/" + f)) }
    guard let obs = inst.results?.first else { continue }
    var best = -1; var bestD = 1e9
    for idx in obs.allInstances {
        let pb = try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: idx), from: h)
        CVPixelBufferLockBaseAddress(pb, .readOnly)
        let w = CVPixelBufferGetWidth(pb), hh = CVPixelBufferGetHeight(pb), st = CVPixelBufferGetBytesPerRow(pb) / 4
        let base = CVPixelBufferGetBaseAddress(pb)!.assumingMemoryBound(to: Float32.self)
        var sx = 0.0, sy = 0.0, n = 0.0
        for y in stride(from: 0, to: hh, by: 4) { for x in stride(from: 0, to: w, by: 4) where base[y * st + x] > 0.5 { sx += Double(x); sy += Double(y); n += 1 } }
        let hit = base[min(hh - 1, Int(py * Double(hh))) * st + min(w - 1, Int(px * Double(w)))] > 0.5
        CVPixelBufferUnlockBaseAddress(pb, .readOnly)
        let d = hit ? -1.0 : (n > 0 ? hypot(sx / n / Double(w) - px, sy / n / Double(hh) - py) : 1e9)
        if d < bestD { bestD = d; best = idx }
    }
    if best >= 0 { try write(try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: best), from: h), W, H, outDir.appendingPathComponent("i/" + f)) }
}
print("done", files.count)
