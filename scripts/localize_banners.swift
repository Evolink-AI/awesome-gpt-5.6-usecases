#!/usr/bin/env swift

import AppKit
import Foundation

struct BannerCopy {
    let locale: String
    let eyebrow: String
    let title: String
    let cta: String
    let titleSize: CGFloat
}

let copies = [
    BannerCopy(locale: "en", eyebrow: "Awesome", title: "GPT 5.6 Use cases", cta: "Click here to use GPT 5.6", titleSize: 76),
    BannerCopy(locale: "es", eyebrow: "Increíbles", title: "Casos de uso de GPT-5.6", cta: "Haz clic aquí para usar GPT-5.6", titleSize: 62),
    BannerCopy(locale: "pt", eyebrow: "Incríveis", title: "Casos de uso do GPT-5.6", cta: "Clique aqui para usar o GPT-5.6", titleSize: 62),
    BannerCopy(locale: "ja", eyebrow: "厳選", title: "GPT-5.6 活用事例", cta: "GPT-5.6 を使う", titleSize: 70),
    BannerCopy(locale: "ko", eyebrow: "엄선", title: "GPT-5.6 활용 사례", cta: "GPT-5.6 사용하기", titleSize: 68),
    BannerCopy(locale: "de", eyebrow: "Beeindruckend", title: "GPT-5.6 Anwendungsfälle", cta: "GPT-5.6 jetzt verwenden", titleSize: 62),
    BannerCopy(locale: "fr", eyebrow: "Remarquables", title: "Cas d’usage de GPT-5.6", cta: "Cliquez ici pour utiliser GPT-5.6", titleSize: 62),
    BannerCopy(locale: "tr", eyebrow: "Harika", title: "GPT-5.6 Kullanım Örnekleri", cta: "GPT-5.6'yı kullanmak için tıklayın", titleSize: 60),
    BannerCopy(locale: "zh-tw", eyebrow: "精選", title: "GPT-5.6 應用案例", cta: "點此使用 GPT-5.6", titleSize: 70),
    BannerCopy(locale: "zh", eyebrow: "精选", title: "GPT-5.6 应用案例", cta: "点击此处使用 GPT-5.6", titleSize: 70),
    BannerCopy(locale: "ru", eyebrow: "Лучшие", title: "Сценарии GPT-5.6", cta: "Нажмите, чтобы использовать GPT-5.6", titleSize: 68),
]

guard CommandLine.arguments.count == 2 else {
    fputs("Usage: localize_banners.swift <repository-root>\n", stderr)
    exit(2)
}

let repoRoot = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let imagesDirectory = repoRoot.appendingPathComponent("images", isDirectory: true)
let templateURL = imagesDirectory.appendingPathComponent("banner-template.png")

guard let template = NSImage(contentsOf: templateURL) else {
    fputs("Missing images/banner-template.png\n", stderr)
    exit(1)
}

let canvasSize = NSSize(width: 1520, height: 760)
let orange = NSColor(calibratedRed: 1.0, green: 0.30, blue: 0.10, alpha: 1)
let eyebrowColor = NSColor(calibratedRed: 0.96, green: 0.57, blue: 0.39, alpha: 1)
let ivory = NSColor(calibratedRed: 0.97, green: 0.94, blue: 0.90, alpha: 1)

func font(locale: String, size: CGFloat, serif: Bool) -> NSFont {
    if !serif {
        return NSFont.systemFont(ofSize: size, weight: .regular)
    }
    if ["ja", "ko", "zh", "zh-tw"].contains(locale) {
        return NSFont.systemFont(ofSize: size, weight: .medium)
    }
    let family = locale == "ru" ? "Times New Roman" : "Bodoni 72"
    return NSFont(name: family, size: size) ?? NSFont.systemFont(ofSize: size, weight: .medium)
}

func drawCentered(
    _ text: String,
    locale: String,
    preferredSize: CGFloat,
    serif: Bool,
    color: NSColor,
    xRange: ClosedRange<CGFloat>,
    centerYFromTop: CGFloat,
    kerning: CGFloat = 0
) {
    var size = preferredSize
    var attributed: NSAttributedString
    repeat {
        attributed = NSAttributedString(
            string: text,
            attributes: [
                .font: font(locale: locale, size: size, serif: serif),
                .foregroundColor: color,
                .kern: kerning,
            ]
        )
        if attributed.size().width <= xRange.upperBound - xRange.lowerBound || size <= 28 {
            break
        }
        size -= 2
    } while true

    let textSize = attributed.size()
    attributed.draw(at: NSPoint(
        x: xRange.lowerBound + ((xRange.upperBound - xRange.lowerBound - textSize.width) / 2),
        y: canvasSize.height - centerYFromTop - (textSize.height / 2)
    ))
}

func drawLocalizedButton(_ copy: BannerCopy) {
    let buttonRect = NSRect(x: 740, y: 278, width: 610, height: 92)
    NSColor.black.setFill()
    NSBezierPath(roundedRect: buttonRect, xRadius: 46, yRadius: 46).fill()

    NSGraphicsContext.saveGraphicsState()
    let shadow = NSShadow()
    shadow.shadowColor = orange.withAlphaComponent(0.85)
    shadow.shadowBlurRadius = 14
    shadow.shadowOffset = .zero
    shadow.set()
    orange.setStroke()
    let border = NSBezierPath(roundedRect: buttonRect, xRadius: 46, yRadius: 46)
    border.lineWidth = 2.5
    border.stroke()
    NSGraphicsContext.restoreGraphicsState()

    drawCentered(
        "\(copy.cta)   →",
        locale: copy.locale,
        preferredSize: 29,
        serif: false,
        color: .white,
        xRange: 775...1320,
        centerYFromTop: 436
    )
}

for copy in copies {
    let outputURL = imagesDirectory.appendingPathComponent("\(copy.locale).png")
    if copy.locale == "en" {
        try Data(contentsOf: templateURL).write(to: outputURL, options: .atomic)
        continue
    }

    guard let bitmap = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(canvasSize.width),
        pixelsHigh: Int(canvasSize.height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ), let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
        fputs("Unable to create a 1520x760 render context\n", stderr)
        exit(1)
    }

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    template.draw(in: NSRect(origin: .zero, size: canvasSize), from: .zero, operation: .copy, fraction: 1)

    NSColor.black.setFill()
    NSBezierPath(rect: NSRect(x: 690, y: 375, width: 810, height: 230)).fill()

    drawCentered(
        copy.eyebrow,
        locale: copy.locale,
        preferredSize: 34,
        serif: false,
        color: eyebrowColor,
        xRange: 715...1465,
        centerYFromTop: 195,
        kerning: 3
    )
    drawCentered(
        copy.title,
        locale: copy.locale,
        preferredSize: copy.titleSize,
        serif: true,
        color: ivory,
        xRange: 715...1465,
        centerYFromTop: 300
    )
    drawLocalizedButton(copy)

    context.flushGraphics()
    NSGraphicsContext.restoreGraphicsState()

    guard let pngData = bitmap.representation(using: .png, properties: [:]) else {
        fputs("Unable to encode banner for \(copy.locale)\n", stderr)
        exit(1)
    }
    try pngData.write(to: outputURL, options: .atomic)
}

print("Rendered \(copies.count) localized banners in \(imagesDirectory.path)")
