{-# LANGUAGE BangPatterns #-}
{-# LANGUAGE BlockArguments #-}
{-# LANGUAGE ImportQualifiedPost #-}
{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE ViewPatterns #-}

--------------------------------------------------------------------------------

import Control.Monad ((<=<))
import Data.List (foldl')
import Data.Text (Text)
import Data.Text qualified as T
import Data.Text.IO qualified as T
import GHC.IO.Handle (BufferMode (NoBuffering), Handle, hSetBuffering)
import Hakyll
import System.Process (runInteractiveCommand)
import Text.Pandoc (Block (..), Extension (..), HTMLMathMethod (..), Inline (..), MathType (..), Pandoc, ReaderOptions (..), WriterOptions (..), extensionsFromList)
import Text.Pandoc.Builder (HasMeta (..), Many, simpleTable)
import Text.Pandoc.Builder qualified as Many (singleton, toList)
import Text.Pandoc.Highlighting (Style, pygments, styleToCss)
import Text.Pandoc.SideNote (usingSideNotes)
import Text.Pandoc.Walk (walk, walkM)

--------------------------------------------------------------------------------
-- Haskyll entrypoint.
main :: IO ()
main = hakyll $ do
  -- Static assets
  match
    ( "images/**"
        .||. "fonts/**"
        .||. "robots.txt"
        .||. "favicon.svg"
        .||. ".well-known/**"
        .||. "CNAME"
        .||. "publickey.txt"
        .||. "pp.jpg"
    )
    $ do
      route idRoute
      compile copyFileCompiler

  -- CSS compression
  match "css/*" $ do
    route idRoute
    compile compressCssCompiler

  -- Bibliography
  match "bib/style.csl" $ compile cslCompiler
  match "bib/bibliography.bib" $ compile biblioCompiler

  -- Non-posts markdown
  match (fromList ["about.rst", "contact.markdown"]) $ do
    route $ setExtension "html"
    compile $
      pandocCompiler'
        >>= loadAndApplyTemplate "templates/default.html" defaultContext
        >>= relativizeUrls

  -- Posts markdown
  match "posts/*" $ do
    route $ setExtension "html"
    compile $
      pandocCompiler'
        >>= loadAndApplyTemplate "templates/post.html" postCtx
        >>= saveSnapshot "content"
        >>= loadAndApplyTemplate "templates/default.html" postCtx
        >>= relativizeUrls

  -- Archive
  create ["archive.html"] $ do
    route idRoute
    compile $ do
      posts <- recentFirst =<< loadAll "posts/*"
      let archiveCtx =
            listField "posts" postCtx (return posts)
              `mappend` constField "title" "Archives"
              `mappend` defaultContext

      makeItem ""
        >>= loadAndApplyTemplate "templates/archive.html" archiveCtx
        >>= loadAndApplyTemplate "templates/default.html" archiveCtx
        >>= relativizeUrls

  -- Atom/RSS Feed
  create ["atom.xml"] $ do
    route idRoute
    compile $ do
      let feedCtx = postCtx `mappend` bodyField "description"
      posts <- fmap (take 10) . recentFirst =<< loadAllSnapshots "posts/*" "content"
      renderAtom myFeedConfiguration feedCtx posts

  -- Syntax Highlighting
  create ["css/syntax.css"] $ do
    route idRoute
    compile $ do
      makeItem $ styleToCss pandocCodeStyle

  -- Root index.html
  match "index.html" $ do
    route idRoute
    compile $ do
      posts <- recentFirst =<< loadAll "posts/*"
      let indexCtx =
            listField "posts" postCtx (return posts)
              `mappend` defaultContext

      getResourceBody
        >>= applyAsTemplate indexCtx
        >>= loadAndApplyTemplate "templates/default.html" indexCtx
        >>= relativizeUrls

  -- Templates
  match "templates/*" $ compile templateBodyCompiler

--------------------------------------------------------------------------------
-- Post context, adds a date to the default context.
postCtx :: Context String
postCtx =
  dateField "date" "%B %e, %Y"
    `mappend` defaultContext

--------------------------------------------------------------------------------

-- RSS
myFeedConfiguration :: FeedConfiguration
myFeedConfiguration =
  FeedConfiguration
    { feedTitle = "Jose Storopoli, PhD",
      feedDescription = "Personal website of Jose Storopoli, PhD",
      feedAuthorName = "Jose Storopoli, PhD",
      feedAuthorEmail = "jose@storopoli.com",
      feedRoot = "https://storopoli.com"
    }

--------------------------------------------------------------------------------
-- COMPILERS --

-- Custom Writer Options
myWriter :: WriterOptions
myWriter =
  defaultHakyllWriterOptions
    { writerHTMLMathMethod = KaTeX "",
      writerHighlightStyle = Just pandocCodeStyle
    }

-- Custom Reader Options
myReader :: ReaderOptions
myReader =
  defaultHakyllReaderOptions
    { readerExtensions =
        readerExtensions defaultHakyllReaderOptions
          <> extensionsFromList [Ext_tex_math_single_backslash]
    }

-- Custom pandoc compiler render functions that work with Item Pandoc
myRenderPandocWithTransformM ::
  ReaderOptions ->
  WriterOptions ->
  (Item Pandoc -> Compiler (Item Pandoc)) ->
  Item String ->
  Compiler (Item String)
myRenderPandocWithTransformM ropt wopt f i =
  writePandocWith wopt <$> (f =<< readPandocWith ropt i)

-- Custom pandoc compiler writer functions that work with Item Pandoc
myPandocCompilerWithTransformM ::
  ReaderOptions ->
  WriterOptions ->
  (Item Pandoc -> Compiler (Item Pandoc)) ->
  Compiler (Item String)
myPandocCompilerWithTransformM ropt wopt f =
  getResourceBody >>= myRenderPandocWithTransformM ropt wopt f

-- Syntax Highlighting
pandocCodeStyle :: Style
pandocCodeStyle = pygments

-- KaTeX server side rendering
hlKaTeX :: Pandoc -> Compiler Pandoc
hlKaTeX pandoc = recompilingUnsafeCompiler do
  (hin, hout, _, _) <- runInteractiveCommand "deno run scripts/math.ts"
  hSetBuffering hin NoBuffering
  hSetBuffering hout NoBuffering

  (`walkM` pandoc) \case
    Math mathType (T.unwords . T.lines . T.strip -> text) -> do
      let math :: Text =
            foldl'
              (\str (repl, with) -> T.replace repl with str)
              case mathType of
                DisplayMath {-s-} -> ":DISPLAY " <> text
                InlineMath {-s-} -> text
              macros
      T.hPutStrLn hin math
      RawInline "html" <$> getResponse hout
    block -> pure block
  where
    -- KaTeX might sent the input back as multiple lines if it involves a
    -- matrix of coordinates. The big assumption here is that it does so only
    -- when matrices—or other such constructs—are involved, and not when it
    -- sends back "normal" HTML.
    getResponse :: Handle -> IO Text
    getResponse handle = go ""
      where
        go :: Text -> IO Text
        go !str = do
          more <- (str <>) <$> T.hGetLine handle
          if ">" `T.isSuffixOf` more -- end of HTML snippet
            then pure more
            else go more

    -- I know that one could supply macros to KaTeX directly, but where is the
    -- fun in that‽
    macros :: [(Text, Text)]
    macros =
      [ ("≔", "\\mathrel{\\vcenter{:}}="),
        ("\\defeq", "\\mathrel{\\vcenter{:}}="),
        ("\\to", "\\longrightarrow"),
        ("\\mapsto", "\\longmapsto"),
        ("\\cat", "\\mathcal"),
        ("\\kVect", "\\mathsf{Vect}_{\\mathtt{k}}")
      ]

-- Bibliography processing
processBib :: Item Pandoc -> Compiler (Item Pandoc)
processBib pandoc = do
  csl <- load "bib/style.csl"
  bib <- load "bib/bibliography.bib"
  -- We do want to link citations.
  p <- withItemBody (pure . setMeta "link-citations" True) pandoc
  fmap tableiseBib <$> processPandocBiblio csl bib p

-- | Align all citations in a table.
tableiseBib :: Pandoc -> Pandoc
tableiseBib = walk \case
  -- Citations start with a <div id="refs" …>
  Div a@("refs", _, _) body ->
    -- No header needed, we just want to fill in the body contents.
    Div a (Many.toList (simpleTable [] (map citToRow body)))
  body -> body
  where
    citToRow :: Block -> [Many Block]
    citToRow =
      map Many.singleton . \case
        Div attr [Para [s1, s2]] ->
          [Div attr [Plain [s1]], Plain [Space], Plain [s2]]
        _ -> error "citToRow: unexpected citation format."

-- Custom pandocCompiler with all compilers
pandocCompiler' :: Compiler (Item String)
pandocCompiler' =
  myPandocCompilerWithTransformM
    myReader
    myWriter
    ( traverse (pure . usingSideNotes <=< hlKaTeX)
        <=< processBib
    )
